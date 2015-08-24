#-*- coding:utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import re
import random
import json
import time
from XCQ import XCQ
from XCWorker import XCWorker
sys.path.append('../base')
import Common as Common
import Config as Config
import Logger as Logger
from RetryCrawler import RetryCrawler
sys.path.append('../db')
from MysqlAccess import MysqlAccess

class XCSpot():
    '''A class of XC spots'''
    def __init__(self, m_type):
        # DB
        self.mysqlAccess   = MysqlAccess()     # mysql access

        # channel queue
        self.chan_queue = XCQ('channel','spot')

        self.work = XCWorker()

        # 默认类别
        self.channel_list = [
                (1,'http://www.ly.com/scenery/scenerysearchlist_22_295__0_0_0_0_0_0_0.html',1)
                ]

        # 页面
        self.site_page  = None

        # 抓取开始时间
        self.begin_time = Common.now()

        # 分布式主机标志
        self.m_type = m_type

    def antPage(self):
        try:
            # 主机器需要配置redis队列
            if self.m_type == 'm':
                val = ('1',)
                channel_list = self.mysqlAccess.selectChannel(val)
                if not channel_list:
                    channel_list = self.channel_list
                if channel_list and len(channel_list) > 0:
                    channel_val_list = []
                    for c in channel_list:
                        channel_val_list.append(c+(self.begin_time,))
                    # 清空channel redis队列
                    self.chan_queue.clearQ()
                    # 保存channel redis队列
                    self.chan_queue.putlistQ(channel_val_list)

                    Common.log('# channel queue end')
                else:
                    Common.log('# not find channel...')

            # channel
            obj = 'channel'
            crawl_type = 'spot'
            _val = (self.begin_time,)
            self.work.process(obj,crawl_type,_val)

        except Exception as e:
            Common.log('# XCSpot antpage error: %s'%e)
            Common.traceback_log()

if __name__ == '__main__':
    loggername = 'channel'
    filename = 'add_spot_%s' % (time.strftime("%Y%m%d%H", time.localtime()))
    Logger.config_logging(loggername, filename)
    args = sys.argv
    #args = ['XCSpot','m']
    if len(args) < 2:
        Common.log('#err not enough args for XCSpot...')
        exit()
    # 是否是分布式中主机
    m_type = args[1]
    j = XCSpot(m_type)
    Common.log('XCSpot start')
    j.antPage()
    time.sleep(1)
    Common.log('XCSpot end')
