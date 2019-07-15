# encoding: UTF-8

from uni_api import *
import time
import json
import urllib
import requests
import numpy as np
import platform


class QA(UniApi):
    def init(self):
        self.subCodes = ['btc_qc'] #订阅的合约

    def onOpenProcess(self): #订阅合约
        for c in self.subCodes:
            self.api.subscribeSpotDepth(c)

    def rtnTick(self,j): #行情
        print j

    def rspQueryAccount(self,o): #账户信息
        print o

    def queryMoney(self):
    	print 'get My spotUserInfo'
    	self.api.spotUserInfo()

    def tradeFuc(self):
        pass


if __name__ == '__main__':

    u = QA() 
    try:
        while 1:
            u.queryMoney()
            time.sleep(10)
    except KeyboardInterrupt:
        u.close()
        aaa = raw_input("have a look : ")
