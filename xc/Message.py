#-*- coding:utf-8 -*-
#!/usr/bin/env python
import sys
sys.path.append('../base')
import Common as Common

@Common.singleton
class Message():
    '''A class of message'''
    def __init__(self):
        pass

    def QueueMsg(self, _obj, _val):
        return self.queueMsg(_val)

    def queueMsg(self, _val):
        msg = {}
        msg["retry"]  = _val[0]
        msg["obj"]    = _val[1]
        msg["type"]   = _val[2]
        msg["val"]    = _val[3:]
        return msg
