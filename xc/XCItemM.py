#-*- coding:utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import time
import random
import traceback
import threading
from Queue import Empty
from Message import Message
from XCItem import Item
sys.path.append('../base')
import Common as Common
import Config as Config
from MyThread  import MyThread
from XCCrawler import XCCrawler
sys.path.append('../dial')
from DialClient import DialClient
sys.path.append('../db')
from MysqlAccess import MysqlAccess
from RedisAccess import RedisAccess
from MongofsAccess import MongofsAccess

import warnings
warnings.filterwarnings("ignore")

class XCItemM(MyThread):
    '''A class of xc item thread manager'''
    def __init__(self, _q_type, thread_num=10, a_val=None):
        # parent construct
        MyThread.__init__(self, thread_num)

        # thread lock
        self.mutex          = threading.Lock()

        self.worker_type    = Config.XC_Spot

        # message
        self.message        = Message()

        # db
        self.mysqlAccess    = MysqlAccess()   # mysql access
        self.mongofsAccess  = MongofsAccess() # mongodb fs access

        # xc queue type
        self._q_type        = _q_type # new:新增商品

        # appendix val
        self.a_val          = a_val
        
        # activity items
        self.items          = []

        # dial client
        self.dial_client    = DialClient()

        # local ip
        self._ip            = Common.local_ip()

        # router tag
        self._tag           = 'ikuai'
        #self._tag          = 'tpent'

        # give up item, retry too many times
        self.giveup_items   = []

    # To dial router
    def dialRouter(self, _type, _obj):
        try:
            _module = '%s_%s' %(_type, _obj)
            self.dial_client.send((_module, self._ip, self._tag))
        except Exception as e:
            Common.log('# To dial router exception: %s' % e)

    def push_back(self, L, v):
        if self.mutex.acquire(1):
            L.append(v)
            self.mutex.release()

    def putItem(self, _item):
        self.put_q((0, _item))

    def putItems(self, _items):
        for _item in _items: self.put_q((0, _item))

    # To crawl retry
    def crawlRetry(self, _data):
        if not _data: return
        _retry, _val = _data
        _retry += 1
        if _retry < Config.item_crawl_retry:
            _data = (_retry, _val)
            self.put_q(_data)
        else:
            self.push_back(self.giveup_items, _val)
            Common.log('# retry too many times, no get item:')
            Common.log(_val)

    # insert item info
    def insertIteminfo(self, iteminfosql_list, f=False):
        if f or len(iteminfosql_list) >= Config.item_max_arg:
            if len(iteminfosql_list) > 0:
                self.mysqlAccess.insertXCItem(iteminfosql_list)
            return True
        return False


    # To crawl item
    def crawl(self):
        # item sql list
        _iteminfosql_list = []
        _itemdaysql_list = []
        _itemhoursql_list = []
        _itemupdatesql_list = []
        while True:
            _data = None
            try:
                try:
                    # 取队列消息
                    _data = self.get_q()
                except Empty as e:
                    # 队列为空，退出
                    # info
                    self.insertIteminfo(_iteminfosql_list, True)
                    _iteminfosql_list = []

                    break

                item = None
                obj = 'item'
                if self._q_type == 'spot':
                    # 新商品实例
                    item = Item()
                    _val = _data[1]
                    if self.a_val: _val = _val + self.a_val
                    item.antPage(_val)
                    # 汇聚
                    self.push_back(self.items, item.outSql())
                
                    # 入库
                    tickets = item.item_tickets
                    if tickets and len(tickets) > 0:
                        self.mysqlAccess.insertXCTicket(tickets)
                    iteminfoSql = item.outSql()
                    _iteminfosql_list.append(iteminfoSql)
                    if self.insertIteminfo(_iteminfosql_list): _iteminfosql_list = []

                # 存网页
                #if item:
                #    _pages = item.outItemPage(obj, self._q_type)
                #    self.mongofsAccess.insertXCPages(_pages)

                # 延时
                time.sleep(1)
                # 通知queue, task结束
                self.queue.task_done()

            except Common.NoItemException as e:
                Common.log('# Not item exception: %s' % e)
                # 通知queue, task结束
                self.queue.task_done()

            except Common.NoPageException as e:
                Common.log('# Not page exception: %s' % e)
                # 通知queue, task结束
                self.queue.task_done()

            except Common.InvalidPageException as e:
                self.crawlRetry(_data)
                Common.log('# Invalid page exception: %s' % e)
                # 通知queue, task结束
                self.queue.task_done()

            except Exception as e:
                Common.log('# Unknown exception crawl item: %s' % e)
                Common.traceback_log()
                self.crawlRetry(_data)
                # 通知queue, task结束
                self.queue.task_done()
                if str(e).find('Name or service not known') != -1 or str(e).find('Temporary failure in name resolution') != -1:
                    Common.log(_data)
                if str(e).find('Read timed out') == -1:
                    # 重新拨号
                    try:
                        self.dialRouter(4, 'item')
                    except Exception as e:
                        Common.log('# DailClient Exception err: %s' % e)
                        time.sleep(10)
                    time.sleep(random.uniform(10,40))


from RedisQueue  import RedisQueue
class XCItemRedisM(MyThread):
    '''A class of xc Item redis queue'''
    def __init__(self, key, q_type, thread_num=10, a_val=None):
        # parent construct
        MyThread.__init__(self, thread_num)
        # thread lock
        self.mutex          = threading.Lock()

        self.xc_type        = Config.XC_TYPE # xc type
        #self.item_type      = q_type        # item queue type

        # db
        self.mysqlAccess    = MysqlAccess() # mysql access
        self.redisQueue     = RedisQueue()  # redis queue
        self.mongofsAccess  = MongofsAccess() # mongodb fs access

        # xc queue type
        self.xc_queue_type  = q_type # new...
        self._key           = key   # redis queue key

        # appendix val
        self.a_val          = a_val

        # return items
        self.items          = []

        # dial client
        self.dial_client    = DialClient()

        # local ip
        self._ip            = Common.local_ip()

        # router tag
        self._tag           = 'ikuai'
        #self._tag          = 'tpent'

        # give up item, retry too many times
        self.giveup_items   = []

    # To dial router
    def dialRouter(self, _type, _obj):
        try:
            _module = '%s_%s' %(_type, _obj)
            self.dial_client.send((_module, self._ip, self._tag))
        except Exception as e:
            Common.log('# To dial router exception: %s' % e)

    def push_back(self, L, v):
        if self.mutex.acquire(1):
            L.append(v)
            self.mutex.release()

    def crawlRetry(self, _key, msg):
        if not msg: return
        msg['retry'] += 1
        _retry = msg['retry']
        _obj = msg["obj"]
        max_time = Config.crawl_retry
        if _obj == 'item':
            max_time = Config.item_crawl_retry
        if _retry < max_time:
            self.redisQueue.put_q(_key, msg)
        else:
            Common.log('# retry too many time, no get msg:')
            Common.log(msg)

    # insert item
    def insertIteminfo(self, iteminfosql_list, f=False):
        if f or len(iteminfosql_list) >= Config.item_max_arg:
            if len(iteminfosql_list) > 0:
                self.mysqlAccess.insertXCItem(iteminfosql_list)
            return True
        return False

    # item sql list
    def crawl(self):
        _iteminfosql_list = []
        i, M = 0, 2
        n = 0
        while True:
            try:
                _data = self.redisQueue.get_q(self._key)

                # 队列为空
                if not _data:
                    # 队列为空，退出
                    # info
                    self.insertIteminfo(_iteminfosql_list, True)
                    _iteminfosql_list = []

                    i += 1
                    if i > M:
                        Common.log('# all get itemQ item num: %d' % n)
                        Common.log('# not get itemQ of key: %s' % self._key)
                        break
                    time.sleep(10)
                    continue
                n += 1
                item = None
                obj = 'item'
                if self.xc_queue_type == 'spot':
                    # 商品实例
                    item = Item()
                    #_val = _data[1]
                    _val = _data["val"]
                    if self.a_val: _val = _val + self.a_val

                    item.antPage(_val)
                    # 汇聚
                    self.push_back(self.items, item.outSql())

                    # 入库
                    tickets = item.item_tickets
                    if tickets and len() > 0:
                        self.mysqlAccess.insertXCTicket(tickets)
                    iteminfoSql = item.outSql()
                    _iteminfosql_list.append(iteminfoSql)
                    if self.insertIteminfo(_iteminfosql_list): _iteminfosql_list = []
                else:
                    continue

                # 存网页
                #if item and obj != '':
                #    _pages = item.outItemPage(obj, self.xc_queue_type)
                #    self.mongofsAccess.insertXCPages(_pages)

                # 延时
                time.sleep(1)

            except Common.NoItemException as e:
                Common.log('# Not item exception: %s' % e)

            except Common.NoPageException as e:
                Common.log('# Not page exception: %s' % e)

            except Common.InvalidPageException as e:
                self.crawlRetry(self._key, _data)
                Common.log('# Invalid page exception: %s' % e)

            except Exception as e:
                Common.log('# Unknown exception crawl item: %s' % e)
                Common.traceback_log()

                self.crawlRetry(self._key, _data)
                if str(e).find('Read timed out') == -1:
                    # 重新拨号
                    try:
                        self.dialRouter(4, 'item')
                    except Exception as e:
                        Common.log('# DailClient Exception err: %s' % e)
                        time.sleep(10)
                    time.sleep(random.uniform(10,30))

if __name__ == '__main__':
    pass

