#-*- coding:utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import traceback
import MysqlPool
sys.path.append('../base')
import Config as Config
import Common as Common

class MysqlAccess():
    '''A class of mysql db access'''
    def __init__(self):
        # 聚划算
        self.xc_db = MysqlPool.g_xcDbPool

    def __del__(self):
        # 聚划算
        self.xc_db = None

    def insertXCItem(self, args_list):
        try:
            sql = 'replace into nd_xc_parser_item_d(crawl_time, item_id, item_name, item_desc, item_url, item_pic_url, item_book_status, item_level, item_area, item_service, item_comment, item_comment_grade, item_oriprice, item_disprice, item_discount, channel_id, position, c_begindate, c_beginhour) values(%s)' % Common.agg(19)
            self.xc_db.executemany(sql, args_list)
        except Exception, e:
            print '# insert xc Item info exception:', e

    def insertXCTicket(self, args_list):
        try:
            sql = 'replace into nd_xc_parser_ticket_d(crawl_time, item_id, item_name, ticket_id, ticket_name, ticket_type, ticket_price, ticket_adprice, ticket_unit_name, ticket_tag, c_begindate, c_beginhour) values(%s)' % Common.agg(12)
            self.xc_db.executemany(sql, args_list)
        except Exception, e:
            print '# insert xc Ticket exception:', e

    def selectChannel(self, args):
        try:
            sql = 'select channel_id, channel_url, channel_type from nd_xc_mid_channel where status = 1 and channel_type = %s'
            return self.xc_db.select(sql, args)
        except Exception, e:
            print '# select xc crawl channel exception:', e

if __name__ == '__main__':
    pass
    #my = MysqlAccess()
