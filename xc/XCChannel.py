#-*- coding:utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import re
import random
import json
import time
import threading
sys.path.append('../base')
import Common as Common
import Config as Config
from XCCrawler import XCCrawler
from RetryCrawler import RetryCrawler

class Channel():
    '''A class of XC channel'''
    def __init__(self):
        # 抓取设置
        self.crawler            = XCCrawler()
        self.retrycrawler       = RetryCrawler()
        self.crawling_time      = Common.now() # 当前爬取时间
        self.crawling_time_s    = Common.time_s(self.crawling_time)
        self.crawling_begintime = '' # 本次抓取开始时间
        self.crawling_beginDate = '' # 本次爬取日期
        self.crawling_beginHour = '' # 本次爬取小时

        # 频道信息
        self.platform           = '携程-pc' # 品牌团所在平台
        self.channel_id         = '' # 频道id
        self.channel_url        = '' # 频道链接
        self.channel_name       = '' # 频道name
        self.channel_type       = '' # 频道类型

        # 频道所属地理位置信息
        self.province_id        = 0  # 省,州id
        self.province_name      = '' # 省,州名称

        # 原数据信息
        self.channel_page       = '' # 频道页面html内容
        self.channel_pages      = {} # 频道页面内请求数据列表

        # channel items
        self.channel_items      = []

        # channel list
        self.channel_list       = []

    # 频道页初始化
    def init(self, channel_id, channel_url, channel_type, begin_time):
        self.channel_id = channel_id
        self.channel_url = channel_url
        self.channel_type = channel_type
        self.crawling_begintime = begin_time
        self.crawling_beginDate = time.strftime("%Y-%m-%d", time.localtime(self.crawling_begintime))
        self.crawling_beginHour = time.strftime("%H", time.localtime(self.crawling_begintime))

    def config(self):
        self.channelPage()
        if self.channel_type == 1:
            self.spot()
        #elif self.channel_type == 2:
        else:
            Common.log('# not find this channel type...')

    def spot(self):
        if self.channel_page:
            m = re.search(r'<div class="cate_select">(.+?)</div>', self.channel_page, flags=re.S)
            if m:
                cate_select = m.group(1)
                c_list = []
                p = re.compile(r'<a.+?class="select">(.+?)</a>', flags=re.S)
                for c in p.finditer(cate_select):
                    c_list.append(re.sub(r'<.+?>', '', c.group(1)).strip())
                self.channel_name = '-'.join(c_list)

            i_p = 1
            i_page = 1
            m_page = 1
            page_main = ''
            m = re.search(r'<div id="base_bd">.+?<div class="bg_miancolor">.+?<div class="vacation_bd">(.+?)<div class="vacation_bd bottom_seo">', self.channel_page, flags=re.S)
            if m:
                page_main = m.group(1)
            else:
                page_main = self.channel_page
            
            Common.log(i_page)
            i_p = self.get_items(page_main, i_p)

            m = re.search(r'<span class="c_page2_numtop">(.+?)</span>', self.channel_page, flags=re.S)
            if m:
                m_page_info = m.group(1)
                m = re.search(r'\d+/(\d+)', m_page_info, flags=re.S)
                if m:
                    m_page = int(m.group(1))

            page_url = self.channel_url[0:-1] + 'P%s/'
            while i_page < m_page:
                i_page += 1
                p_url = page_url % str(i_page)
                Common.log(i_page)
                page = self.retrycrawler.getData(p_url, self.channel_url)
                i_p = self.get_items(page, i_p)

    def get_items(self, page_main, i_p):
        if page_main:
            p = re.compile(r'<div class="searchresult_product04">\s+<div class="search_ticket_caption basefix">\s+<a href="(.+?)".+?>\s+<img src="(.+?)".+?/>.+?<div class="search_ticket_title">\s+<h2>\s+<a.+?>(.+?)</a>.+?</h2>\s+<div class="adress">(.+?)</div>\s+<div class="exercise">(.*?)</div>', flags=re.S)
            for info in p.finditer(page_main):
                if int(self.channel_type) == 1:
                    i_url = Config.xc_piao_home + info.group(1)
                else:
                    i_url = Config.xc_home + info.group(1)
                i_img, i_name, i_area, i_desc = info.group(2), info.group(3).strip(), info.group(4).strip(), info.group(5).strip()
                i_book = 1
                i_id = 0
                if i_url != '':
                    m = re.search(r't(\d+).html', i_url)
                    if m:
                        i_id = m.group(1)
                    val = (self.channel_id, self.channel_name, self.channel_url, self.channel_type, (i_book, i_id, i_url, i_img, i_name, i_desc, i_area, i_p, self.crawling_begintime))
                    self.channel_items.append(val)
                i_p += 1
        return i_p

    def channelList(self): 
        self.channelPage()
        if self.channel_page:
            m = re.search(r'<ul class="search_cate">\s+<li class="cate_content.+?">\s+<span class="b">.+?<span class="area_box">(.+?)</span>', self.channel_page, flags=re.S)
            if m:
                area_infos = m.group(1)
                p = re.compile(r'<a href="(.+?)".+?>(.+?)</a>', flags=re.S)
                for area in p.finditer(area_infos):
                    channel_url, c_name = Config.xc_piao_home + area.group(1), area.group(2)
                    channel_id = 0
                    if channel_url:
                        m = re.search(r'D(\d+)', channel_url)
                        if m:
                            channel_id = m.group(1)
                    if c_name:
                        m = re.search(r'(.+?)\(', c_name, flags=re.S)
                        if m:
                            channel_name = m.group(1).strip()
                        else:
                            channel_name = c_name.strip()
                    if int(channel_id) != 0 and channel_url:
                        self.channel_list.append((channel_id, channel_name, channel_url, str(self.channel_type), str(self.province_id), self.province_name))
                    
    def channelPage(self):
        if self.channel_url:
            refers = Config.xc_home
            if int(self.channel_type) == 1:
                refers = Config.xc_piao_home
            data = self.crawler.getData(self.channel_url, Config.xc_home)
            if not data and data == '': raise Common.InvalidPageException("# channelPage:not find channel page,channel_id:%s,channel_url:%s"%(str(self.channel_id), self.channel_url))
            if data and data != '':
                self.channel_page = data
                self.channel_pages['channel-home'] = (self.channel_url, data)

    def antPage(self, val):
        channel_id, channel_url, channel_type, begin_time = val
        self.init(channel_id, channel_url, channel_type, begin_time)
        self.config()

    def antChannelList(self, val):
        self.channel_url, self.channel_type, self.province_id, self.province_name = val
        self.channelList()


if __name__ == '__main__':
    Common.log(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    c = Channel()
    #val = (1,'http://piao.ctrip.com/dest/p-shandong-10/s-tickets/A110D169/', 1, Common.now())
    #c.antPage(val)
    val = ('http://piao.ctrip.com/dest/p-shandong-10/s-tickets/A110/', 1)
    c.antChannelList(val)
    for val in c.channel_list:
        Common.log(val)
    time.sleep(1)
    Common.log(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

