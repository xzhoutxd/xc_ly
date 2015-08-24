#-*- coding:utf-8 -*-
#!/usr/bin/env python

from sys import path

from hotqueue import HotQueue
path.append(r'../base')
import Environ as Environ
import Common  as Common

class RedisQueue:
    def __init__(self):
        # redis数据库设置
        self.QUEUE_DB = 100

        # redis配置
        self.redis_ip, self.redis_port, self.redis_passwd = Environ.redis_config[self.QUEUE_DB]

        # 抓取队列   tc:100, xc:101
        self.q_list = [
                '101_channel_spot',  # 携程频道门票
                '101_item_spot' # 携程门票
            ]

        # 初始化队列
        self.initQueue()

    def initQueue(self):
        # hotqueue队列字典表
        self.q_dict = {}

        # 抓取队列
        for q in self.q_list:
            self.q_dict[q] = HotQueue(q, host=self.redis_ip, port=self.redis_port, password=self.redis_passwd, db=self.QUEUE_DB)

    # To put queue
    def put_q(self, _key, _val):
        try:
            if self.q_dict.has_key(_key):
                q = self.q_dict[_key]
                q.put(_val)
        except Exception as e:
            Common.log('# put_q exception: %s' % e)

    # To get queue
    def get_q(self, _key):
        _val = None
        try:
            if self.q_dict.has_key(_key):
                q = self.q_dict[_key]
                _val = q.get()
        except Exception as e:
            Common.log('# get_q exception: %s' % e)
        return _val

    # 清空队列
    def clear_q(self, _key):
        if self.q_dict.has_key(_key):
            q = self.q_dict[_key]
            q.clear()

if __name__ == "__main__":
    pass

