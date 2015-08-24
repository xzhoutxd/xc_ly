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
from XCTicket import Ticket

class Item():
    '''A class of xc Item'''
    def __init__(self):
        # 商品页面抓取设置
        self.crawler            = XCCrawler()
        self.crawling_time      = Common.now() # 当前爬取时间
        self.crawling_begintime = '' # 本次抓取开始时间
        self.crawling_beginDate = '' # 本次爬取日期
        self.crawling_beginHour = '' # 本次爬取小时

        # 单品类型商品所属频道
        self.channel_id         = ''
        self.channel_name       = ''
        self.channel_url        = ''
        self.channel_type       = ''
        self.item_position      = 0

        # 商品信息
        self.item_id            = '' # 商品Id
        self.item_url           = '' # 商品链接
        self.item_pic_url       = '' # 商品展示图片链接
        self.item_name          = '' # 商品Name
        self.item_desc          = '' # 商品说明
        self.item_book_status   = 1  # 商品是否售卖 0:不售,1:在售
        self.item_level         = '' # 级别
        self.item_area          = '' # 地址
        self.item_service       = '' # 服务
        self.item_comment       = '' # 评论数
        self.item_comment_grade = '' # 评分

        # 商品交易
        self.item_oriprice      = '' # 商品原价
        self.item_disprice      = '' # 商品折扣价
        self.item_discount      = '' # 商品打折

        # 门票
        self.item_tickets       = []

        # 原数据信息
        self.item_pageData      = '' # 商品所属数据项内容
        self.item_page          = '' # 商品页面html内容
        self.item_pages         = {} # 商品页面内请求数据列表


    # 商品页信息
    def spotConfig(self, _val):
        self.item_book_status, self.item_id, self.item_url, self.item_pic_url, self.item_name, self.item_desc, self.item_area, self.item_position, self.crawling_begintime = _val
        # 本次抓取开始日期
        self.crawling_beginDate = time.strftime("%Y-%m-%d", time.localtime(self.crawling_begintime))
        # 本次抓取开始小时
        self.crawling_beginHour = time.strftime("%H", time.localtime(self.crawling_begintime))
        if self.item_book_status == 1:
            # 商品页信息
            self.itemPage()
            page = self.item_page
            self.item_pages['item-home'] = (self.item_url, self.item_page)

            m = re.search(r'<div class="media-price".+?>.+?<div class="price-box">.+?<span>(\d+)</span>', page, flags=re.S)
            if m:
                self.item_disprice = m.group(1)

            m = re.search(r'<li class="promise".+?>(.+?)</li>', page, flags=re.S)
            if m:
                s_service = m.group(1)
                promise_list = []
                p = re.compile(r'<div id="J-MediaLabel" class="media-label-wrapper">\s+<span class="media-label">(.+?)</span>', flags=re.S)
                for promise in p.finditer(s_service):
                    promise_list.append(promise.group(1))
                self.item_service = ';'.join(promise_list)

            m = re.search(r'<div class="grade" id="J-grade" data-value="(.+?)".+?>', page, flags=re.S)
            if m:
                self.item_comment_grade = m.group(1)
            m = re.search(r'<div class="grade".+?>.+?<a href=".+?" class="mark goToAnchor" data-target="J-Yhdp">(.+?)</a></div>', page, flags=re.S)
            if m:
                s_comment = m.group(1)
                m = re.search(r'(\d+)', s_comment)
                if m:
                    self.item_comment = m.group(1)

            m = re.search(r'<span class="media-grade" style="">(.+?)</span>', page, flags=re.S)
            if m:
                self.item_level = re.sub(r'<.+?>', '', m.group(1)).strip()
            
            self.itemTicket()

    def itemTicket(self):
        if self.item_page:
            m = re.search(r'<div id="J-Ticket" class="tab-content">\s+<table class="ticket-table">.+?<tbody>(.+?)</tbody>\s+</table>', self.item_page, flags=re.S)
            if m: 
                infos = m.group(1)
                t_type = ''
                t_i = 1
                p = re.compile(r'<tr class="ticket-info.+?" data-id="(.*?)".+?>(.+?)</tr>', flags=re.S)
                for info in p.finditer(infos):
                    t_id, t_data = info.group(1), info.group(2)
                    if not t_id or t_id == '':
                        t_id = t_i
                    val = (self.item_id, self.item_name, self.channel_type, t_type, t_id, t_data, self.crawling_begintime)
                    t = Ticket()
                    t.antPage(val)
                    self.item_tickets.append(t.outSql())
                    t_i += 1
                    t_type = t.ticket_type
                                    
    # 商品详情页html
    def itemPage(self):
        if self.item_url != '':
            refer_url = self.channel_url
            page = self.crawler.getData(self.item_url, refer_url)

            if type(self.crawler.history) is list and len(self.crawler.history) != 0 and re.search(r'302',str(self.crawler.history[0])):
                if not self.itempage_judge(page):
                    Common.log('#crawler history:')
                    Common.log(self.crawler.history)
                    raise Common.NoPageException("# itemPage: not find item page, redirecting to other page,id:%s,item_url:%s"%(str(self.item_id), self.item_url))

            if not page or page == '':
                Common.log('#crawler history:')
                Common.log(self.crawler.history)
                raise Common.InvalidPageException("# itemPage: find item page empty,id:%s,item_url:%s"%(str(self.item_id), self.item_url))
            self.item_page = page
        else:
            raise Common.NoPageException("# itemPage: not find item page, url is null,id:%s,item_url:%s"%(str(self.item_id), self.item_url))

    # 执行
    def antPage(self, val):
        self.channel_id, self.channel_name, self.channel_url, self.channel_type, i_val = val
        if self.channel_type == 1:
            self.spotConfig(i_val)

    def outTuple(self):
        return (self.channel_id, self.channel_name, self.channel_url, self.channel_type, self.item_position, self.item_book_status, self.item_id, self.item_url, self.item_pic_url, self.item_name, self.item_desc, self.item_level, self.item_area, self.item_service, self.item_comment, self.item_comment_grade, self.item_oriprice, self.item_disprice, self.item_discount, self.crawling_beginDate, self.crawling_beginHour)

    def outSql(self):
        return (Common.time_s(float(self.crawling_time)), str(self.item_id), self.item_name, self.item_desc, self.item_url, self.item_pic_url, str(self.item_book_status), self.item_level, self.item_area, self.item_service, str(self.item_comment), str(self.item_comment_grade), str(self.item_oriprice), str(self.item_disprice), str(self.item_discount), str(self.channel_id), str(self.item_position), self.crawling_beginDate, self.crawling_beginHour)

if __name__ == '__main__':
    Common.log(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    i = Item()
    #val = (1, '\xe5\x8c\xba\xe5\x9f\x9f\xe5\xb1\xb1\xe4\xb8\x9c-\xe6\x99\xaf\xe5\x8c\xba\xe5\xa8\x81\xe6\xb5\xb7', 'http://piao.ctrip.com/dest/p-shandong-10/s-tickets/A110D169/', 1, (1, '1409966', 'http://piao.ctrip.com/dest/t1409966.html', 'http://dimg02.c-ctrip.com/images/tg/845/837/967/052a21530763433e9b985dae4427f911_C_186_105.jpg', '\xe3\x80\x8a\xe7\xa5\x9e\xe6\xb8\xb8\xe5\x8d\x8e\xe5\xa4\x8f\xe3\x80\x8b\xe5\xb1\xb1\xe6\xb0\xb4\xe5\xae\x9e\xe6\x99\xaf\xe6\xbc\x94\xe5\x87\xba', '\xe7\x89\xb9\xe8\x89\xb2\xef\xbc\x9a\xe2\x98\x85\xe4\xb8\x96\xe7\x95\x8c\xe9\xa6\x96\xe9\x83\xa8360\xe5\xba\xa6\xe5\x85\xa8\xe6\x96\xb9\xe4\xbd\x8d\xe5\xb1\xb1\xe6\xb0\xb4\xe5\xae\x9e\xe6\x99\xaf\xe6\xbc\x94\xe5\x87\xba\xe3\x80\x82', '\xe5\x9c\xb0\xe5\x9d\x80\xef\xbc\x9a\xe5\xb1\xb1\xe4\xb8\x9c\xe5\xa8\x81\xe6\xb5\xb7\xe5\xb8\x82\xe5\x8d\x8e\xe5\xa4\x8f\xe8\xb7\xaf1\xe5\x8f\xb7\xe3\x80\x82', 1, Common.now()))
    val = (1, '\xe5\x8c\xba\xe5\x9f\x9f\xe5\xb1\xb1\xe4\xb8\x9c-\xe6\x99\xaf\xe5\x8c\xba\xe5\xa8\x81\xe6\xb5\xb7', 'http://piao.ctrip.com/dest/p-shandong-10/s-tickets/A110D169/', 1, (1, '1409636', 'http://piao.ctrip.com/dest/t1409636.html', 'http://dimg02.c-ctrip.com/images/fd/tg/g1/M09/23/12/CghzflVuXT-AIPsUAAPVgUa7s1E792_C_186_105.jpg', '\xe2\x80\x9c\xe4\xbe\xa8\xe4\xb9\xa1\xe5\x8f\xb7\xe2\x80\x9d\xe6\xb8\xb8\xe8\xbd\xae', '\xe7\x89\xb9\xe8\x89\xb2\xef\xbc\x9a\xe2\x98\x85 \xe5\xa8\x81\xe6\xb5\xb7\xe6\xb9\xbe\xe5\x85\xa8\xe6\x99\xaf\xe5\xbc\x8f\xe4\xbc\x91\xe9\x97\xb2\xe8\xa7\x82\xe5\x85\x89\xe6\xb8\xb8\xe8\xbd\xae\xe3\x80\x82', '\xe5\x9c\xb0\xe5\x9d\x80\xef\xbc\x9a\xe5\xb1\xb1\xe4\xb8\x9c\xe7\x9c\x81\xe5\xa8\x81\xe6\xb5\xb7\xe5\xb8\x82\xe6\xb5\xb7\xe6\xbb\xa8\xe5\x8c\x97\xe8\xb7\xaf53\xe5\x8f\xb7\xef\xbc\x88\xe5\x88\x98\xe5\x85\xac\xe5\xb2\x9b\xe7\xa0\x81\xe5\xa4\xb4\xe5\x8c\x97100\xe7\xb1\xb3\xe5\xa8\x81\xe6\xb5\xb7\xe8\x80\x81\xe6\xb8\xaf\xe5\xae\xa2\xe8\xbf\x90\xe7\xa0\x81\xe5\xa4\xb4\xe9\x99\xa2\xe5\x86\x85\xef\xbc\x89\xe3\x80\x82', 2, Common.now()))

    i.antPage(val)
    i_val = i.outTuple()
    for s in i_val:
        Common.log(s)

    for t in i.item_tickets:
        Common.log(t)
    time.sleep(1)
    Common.log(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


