#-*- coding:utf-8 -*-
#!/usr/bin/env python

from sys import path

import json
import pickle
from RedisPool import RedisPool
path.append(r'../base')
import Common as Common

@Common.singleton
class RedisAccess:
    def __init__(self):
        # redis db instance
        self.redis_pool = RedisPool()

        # redis db id
        self.DEFAULT_DB    = 0   # default db
        
        self.XC_ITEM_DB    = 210 # xc item

        self.COOKIE_DB     = 9   # cookie

    ######################## Cookie部分 ########################

    # 判断是否存在cookie
    def exist_cookie(self, keys):
        return self.redis_pool.exists(keys, self.COOKIE_DB)

    # 删除cookie
    def remove_cookie(self, keys):
        return self.redis_pool.remove(keys, self.COOKIE_DB)

    # 查询cookie
    def read_cookie(self, keys):
        try:
            val = self.redis_pool.read(keys, self.COOKIE_DB)
            if val:
                cookie_dict = pickle.loads(val)
                _time  = cookie_dict["time"]            
                _cookie= cookie_dict["cookie"]
                return (_time, _cookie)
        except Exception, e:
            Common.log('# Redis access read cookie exception: %s' % e)
            return None

    # 写入cookie
    def write_cookie(self, keys, val):
        try:
            _time, _cookie = val
            cookie_dict = {}
            cookie_dict["time"]   = _time
            cookie_dict["cookie"] = _cookie
            cookie_json = pickle.dumps(cookie_dict)
            
            self.redis_pool.write(keys, cookie_json, self.COOKIE_DB)
        except Exception, e:
            Common.log('# Redis access write cookie exception: %s' % e)

    # 扫描cookie
    def scan_cookie(self):
        try:
            cookie_list = []
            cookies = self.redis_pool.scan_db(self.COOKIE_DB)
            for cookie in cookies:
                val = cookie[1]
                if val:
                    cookie_dict = pickle.loads(val)
                    _time   = cookie_dict["time"]   
                    _cookie = cookie_dict["cookie"]
                    cookie_list.append((_time, _cookie))
            return cookie_list
        except Exception, e:
            Common.log('# Redis access scan cookie exception: %s' % e)
            return None

    ######################## XC ITEM ###################

    # 判断是否存在xc item
    def exist_xcitem(self, keys):
        return self.redis_pool.exists(keys, self.XC_ITEM_DB)

    # 删除xc item
    def delete_xcitem(self, keys):
        self.redis_pool.remove(keys, self.XC_ITEM_DB)

    # 查询xc item
    def read_xcitem(self, keys):
        try:
            val = self.redis_pool.read(keys, self.XC_ITEM_DB)
            return json.loads(val) if val else None 
        except Exception, e:
            Common.log('# Redis access read xc item exception: %s' % e)
            return None

    # 写入xc item
    def write_xcitem(self, keys, val):
        try:
            item_json = json.dumps(val)
            self.redis_pool.write(keys, item_json, self.XC_ITEM_DB)
        except Exception, e:
            Common.log('# Redis access write xc item exception: %s' % e)

    # 扫描xc item - 性能不好
    def scan_xcitem(self):
        try:
            for item in self.redis_pool.scan_db(self.XC_ITEM_DB):
                key, val = item
                if not val: continue
                item_dict    = json.loads(val)
                #Common.log("# scan_xcitem %s:" %key)
                #Common.log(item_dict)
        except Exception as e:
            Common.log('# Redis access scan xc item exception: %s' % e)


if __name__ == '__main__':
    pass


