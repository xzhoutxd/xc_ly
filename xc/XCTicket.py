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
import threading
import hashlib
sys.path.append('../base')
import Common as Common
import Config as Config
from XCCrawler import XCCrawler

class Ticket():
    '''A class of xc Ticket'''
    def __init__(self):
        # 商品页面抓取设置
        self.crawler            = XCCrawler()
        self.crawling_time      = Common.now() # 当前爬取时间
        self.crawling_begintime = '' # 本次抓取开始时间
        self.crawling_beginDate = '' # 本次爬取日期
        self.crawling_beginHour = '' # 本次爬取小时

        # 门票所属商品信息
        self.item_id            = '' # 商品Id
        self.item_name          = '' # 商品Name
        self.item_type          = '' # 商品类型

        # 门票类型
        self.ticket_type        = '' # 门票类型

        # 门票信息
        self.ticket_id          = '' # 门票id
        self.ticket_name        = '' # 门票名称
        self.ticket_price       = '' # 门票价
        self.ticket_adprice     = '' # 门票活动价
        self.ticket_unit_name   = '' # 门票(套票 单票 套餐等信息)
        self.ticket_tag         = '' # 门票特点

        # 数据信息
        self.ticket_pages       = {}


    def ticketConfig(self, t_data):
        if t_data:
            m = re.search(r'<td class="ticket-type".+?>\s+<span>(.+?)</span>', t_data, flags=re.S)
            if m:
                self.ticket_type = m.group(1)
            m = re.search(r'<td class="ticket-title-wrapper">\s+<span>(.+?)</span><a href=".+?" class="ticket-title">(.+?)<i>', t_data, flags=re.S)
            if m:
                self.ticket_unit_name, self.ticket_name = m.group(1), m.group(2)
            m = re.search(r'<td class="del-price">.+?<strong>(.+?)</strong>', t_data, flags=re.S)
            if m:
                self.ticket_price = m.group(1)
            m = re.search(r'<td class="ctrip-price">.+?<strong>(.+?)</strong>', t_data, flags=re.S)
            if m:
                self.ticket_adprice = m.group(1)
            tags = []
            p = re.compile(r'<span class="icon-back">(.+?)</span>', flags=re.S)
            for icon in p.finditer(t_data):
                tags.append(re.sub(r'<.+?>', '', Common.htmlDecode(icon.group(1))).strip())
            p = re.compile(r'<span class="icon-mobile has-word">(.+?)</span>', flags=re.S)
            for icon in p.finditer(t_data):
                tags.append('手机' + re.sub(r'<.+?>', '', Common.htmlDecode(icon.group(1))).strip())
            if tags and len(tags) > 0:
                self.ticket_tag = ';'.join(tags)
        

            self.ticket_pages['item-init'] = ('', t_data)


    def antPage(self, val):
        self.item_id, self.item_name, self.item_type, self.ticket_type, self.ticket_id, t_data, self.crawling_begintime = val
        # 本次抓取开始日期
        self.crawling_beginDate = time.strftime("%Y-%m-%d", time.localtime(self.crawling_begintime))
        # 本次抓取开始小时
        self.crawling_beginHour = time.strftime("%H", time.localtime(self.crawling_begintime))
        self.ticketConfig(t_data)
        

    def outTuple(self):
        return (self.item_id, self.item_name, self.item_type, self.ticket_type, self.ticket_id, self.ticket_name, self.ticket_price, self.ticket_adprice, self.ticket_unit_name, self.ticket_tag, self.crawling_beginDate, self.crawling_beginHour)

    def outSql(self):
        return (Common.time_s(float(self.crawling_time)), self.item_id, self.item_name, self.ticket_id, self.ticket_name, self.ticket_type, self.ticket_price, self.ticket_adprice, self.ticket_unit_name, self.ticket_tag, self.crawling_beginDate, self.crawling_beginHour)
