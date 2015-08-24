#-*- coding:utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import re
import random
import json
import time
import traceback
import logging
from Message import Message
from XCChannel import Channel
from XCItemM import XCItemM
#from XCItemM import XCItemRedisM
sys.path.append('../base')
import Common as Common
import Config as Config
import Logger as Logger
from XCCrawler import XCCrawler
sys.path.append('../dial')
from DialClient import DialClient
sys.path.append('../db')
from MysqlAccess import MysqlAccess
from RedisQueue  import RedisQueue
from RedisAccess import RedisAccess
from MongofsAccess import MongofsAccess

class XCWorker():
    '''A class of xc worker'''
    def __init__(self):
        # xc spot type
        self.worker_type   = Config.XC_Spot
        # DB
        self.xc_type       = Config.XC_TYPE    # queue type
        self.mysqlAccess   = MysqlAccess()     # mysql access
        self.redisQueue    = RedisQueue()      # redis queue
        self.mongofsAccess = MongofsAccess()   # mongodb fs access

        # 抓取设置
        self.crawler       = XCCrawler()

        # message
        self.message       = Message()

        # 抓取时间设定
        self.crawling_time = Common.now() # 当前爬取时间
        self.begin_time    = Common.now()
        self.begin_date    = Common.today_s()
        self.begin_hour    = Common.nowhour_s()

    def init_crawl(self, _obj, _crawl_type):
        self._obj          = _obj
        self._crawl_type   = _crawl_type

        # dial client
        self.dial_client   = DialClient()

        # local ip
        self._ip           = Common.local_ip()

        # router tag
        self._router_tag   = 'ikuai'
        #self._router_tag  = 'tpent'

        # items
        self.items         = []

        # giveup items
        self.giveup_items  = []

        # giveup msg val
        self.giveup_val    = None
        self.init_log(_obj, _crawl_type)

    def init_log(self, _obj, _crawl_type):
        if not Logger.logger:
            loggername = 'other'
            filename = 'crawler_%s' % (time.strftime("%Y%m%d%H", time.localtime(self.begin_time)))
            if _obj == 'channel':
                loggername = 'channel'
                filename = 'add_%s_%s' % (_crawl_type,time.strftime("%Y%m%d%H", time.localtime(self.begin_time)))
            #elif _obj == 'item':
                
            Logger.config_logging(loggername, filename)

    # To dial router
    def dialRouter(self, _type, _obj):
        try:
            _module = '%s_%s' %(_type, _obj)
            self.dial_client.send((_module, self._ip, self._router_tag))
        except Exception as e:
            Common.log('# To dial router exception: %s' % e)

    # To crawl retry
    def crawlRetry(self, _key, msg):
        if not msg: return
        msg['retry'] += 1
        _retry = msg['retry']
        _obj = msg["obj"]
        max_time = Config.crawl_retry
        if _obj == 'channel':
            max_time = Config.channel_crawl_retry
        elif _obj == 'item':
            max_time = Config.item_crawl_retry
        if _retry < max_time:
            self.redisQueue.put_q(_key, msg)
        else:
            #self.push_back(self.giveup_items, msg)
            Common.log("# retry too many time, no get msg:")
            Common.log(msg)

    # To crawl page
    def crawlPage(self, _obj, _crawl_type, _key, msg, _val):
        try:
            if _obj == 'channel':
                self.run_channel(msg)
            else:
                Common.log('# crawlPage unknown obj = %s' % _obj)
        except Common.InvalidPageException as e:
            Common.log('# Invalid page exception: %s' % e)
            self.crawlRetry(_key,msg)
        except Common.DenypageException as e:
            Common.log('# Deny page exception: %s' % e)
            self.crawlRetry(_key,msg)
            # 重新拨号
            try:
                self.dialRouter(4, 'chn')
            except Exception as e:
                Common.log('# DailClient Exception err: %s' % e)
                time.sleep(random.uniform(10,30))
            time.sleep(random.uniform(10,30))
        except Common.SystemBusyException as e:
            Common.log('# System busy exception: %s' % e)
            self.crawlRetry(_key,msg)
            time.sleep(random.uniform(10,30))
        except Common.RetryException as e:
            Common.log('# Retry exception: %s' % e)
            if self.giveup_val:
                msg['val'] = self.giveup_val
            self.crawlRetry(_key,msg)
            time.sleep(random.uniform(20,30))
        except Exception as e:
            Common.log('# exception err: %s' % e)
            self.crawlRetry(_key,msg)
            Common.traceback_log()
            if str(e).find('Read timed out') == -1:
                # 重新拨号
                try:
                    self.dialRouter(4, 'chn')
                except Exception as e:
                    Common.log('# DailClient Exception err: %s' % e)
                time.sleep(random.uniform(10,30))

    def run_channel(self, msg):
        msg_val = msg["val"]
        c = Channel()
        c.antPage(msg_val)
        #self.items = c.channel_items
        self.run_items(c)

    # 并行获取商品
    def run_items(self, chan):
        Common.log('# Items start, channel_id:%s, channel_name:%s' % (str(chan.channel_id), chan.channel_name))
        # 多线程 控制并发的线程数
        Common.log('# Items num: %d' % len(chan.channel_items))
        if len(chan.channel_items) > Config.item_max_th:
            m_itemsObj = XCItemM(self._crawl_type, Config.item_max_th)
        else:
            m_itemsObj = XCItemM(self._crawl_type, len(chan.channel_items))
        m_itemsObj.createthread()
        m_itemsObj.putItems(chan.channel_items)
        m_itemsObj.run()

        item_list = m_itemsObj.items
        Common.log('# find Items num: %d' % len(chan.channel_items))
        Common.log('# crawl Items num: %d' % len(item_list))
        giveup_items = m_itemsObj.giveup_items
        if len(giveup_items) > 0:
            Common.log('# giveup Items num: %d' % len(giveup_items))
            raise Common.RetryException('# run_items: some items retry more than max times..')
        Common.log('# Items end, channel_id:%s, channel_name:%s' % (str(chan.channel_id), chan.channel_name))

    def process(self, _obj, _crawl_type, _val=None):
        #self.processMulti(_obj, _crawl_type, _val)
        self.processOne(_obj, _crawl_type, _val)

    def processOne(self, _obj, _crawl_type, _val=None):
        self.init_crawl(_obj, _crawl_type)

        i, M = 0, 20
        if _obj == 'channel':
            M = 2
        n = 0
        while True:
            if _crawl_type and _crawl_type != '':
                _key = '%s_%s_%s' % (self.xc_type,_obj,_crawl_type)
            else:
                _key = '%s_%s' % (self.xc_type,_obj)
            _msg = self.redisQueue.get_q(_key)

            # 队列为空
            if not _msg:
                i += 1
                if i > M:
                    Common.log('# not get queue of key: %s' % _key)
                    Common.log('# all get num of item in queue: %d' % n)
                    break
                time.sleep(10)
                continue
            n += 1
            try:
                self.crawlPage(_obj, _crawl_type, _key, _msg, _val)
            except Exception as e:
                Common.log('# exception err in process of XCWorker: %s , key: %s' % (e,_key))
                Common.log(_msg)

    def processMulti(self, _obj, _crawl_type, _val=None):
        self.init_crawl(_obj, _crawl_type)
        if _crawl_type and _crawl_type != '':
            _key = '%s_%s_%s' % (self.xc_type,_obj,_crawl_type)
        else:
            _key = '%s_%s' % (self.xc_type,_obj)

        try:
            self.crawlPageMulti(_obj, _crawl_type, _key,  _val)
        except Exception as e:
            Common.log('# exception err in processMulti of XCWorker: %s, key: %s' % (e,_key))

    # To crawl page
    def crawlPageMulti(self, _obj, _crawl_type, _key, _val):
        self.run_multiitems(_key, _val)
        #Common.log('# crawlPageMulti unknown obj = %s' % _obj)

    def run_multiitems(self, _key, _val):
        mitem = XCItemRedisM(_key, self._crawl_type, 20, _val)
        mitem.createthread()
        mitem.run()
        item_list = mitem.items
        Common.log('# crawl Items num: %d' % len(item_list))

if __name__ == '__main__':
    pass

