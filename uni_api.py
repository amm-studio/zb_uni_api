from zb_ws import *
import json

import sys
import yaml

import logging
import traceback

logger = logging.getLogger("UniApi")

formatter = logging.Formatter('%(asctime)s - %(filename)s [%(lineno)d] - %(levelname)s - %(message)s')

file_handler = logging.FileHandler("custom.log")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.formatter = formatter

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.setLevel(logging.INFO)


class UniApi(object):

    def __init__(self,apiKey,secretKey):
        self.orderMap  = {}
        self.orderMapDis  = {}

        self.poiTs = time.time()

        self.api = ZB_Sub_Spot_Api(apiKey, secretKey,self.onMessage)
        self.api.onOpenProcess = self.onOpenProcess

        logger.debug('UniApi init!!!')

        while self.api.connectd == False:
            pass

    def onOpenProcess(self):
        pass

    def onMessage(self,mess):
        js = json.loads(mess)

        if js['channel'].find('_getorders') > -1:
            self.rspQueryOrders(js)

        elif js['channel'].find('_order') > -1:
            self.parseOrder(js)

        elif js['channel'].find('_depth') > -1:
            self.rtnTick(js)

        elif js['channel'].find('_cancelorder') > -1:
            self.rspCancelOrder(js)
            pass #self.parseOrder(js)

        elif js['channel'].find('_getorder') > -1 and self.rspQueryOrder != None:
            self.rspQueryOrder(js)

        elif js['channel'].find('getaccountinfo') > -1:
            self.poiTs = time.time()
            self.rspQueryAccount(js)


    def rspQueryAccount(self,o):
        pass

    def rspCancelOrder(self,o):
        pass

    def TradeCommit(self,inst,direct,price,vol):
        return self.api.order(inst.lower(),direct,price,vol)


    def TradeCancel(self,inst,order_id):
        return self.api.cancel(inst.lower(),str(order_id))

    def TradeCancelByHash(self,hash_id):
        logger.debug( 'TradeCancelByHash:%s' %hash_id)

        if not self.orderMap.has_key(hash_id):
            return None
        order = self.orderMap[hash_id]
        oid = order['data']['entrustId']

        logger.debug( '-cancel :%s' %order)
        inst = order['channel'].replace('_order','')
       
        return self.api.cancel(inst.lower(),str(oid))

    def QueryOrder(self,inst,order_id):
        return self.api.getOrder(inst,order_id)

    def QueryOrderByHash(self,hash_id):
        if not self.orderMap.has_key(hash_id):
            return None

        order = self.orderMap[hash_id]
        oid = order['data']['entrustId']

        logger.debug( '-queryOrder :%s' %order)
        inst = order['channel'].replace('_order','')

        return self.api.getOrder(inst.lower(),str(oid))

    def rspQueryOrders(self,order):
        logger.debug( 'rspQueryOrders:%s' %order)

        if self.rtnOrders != None:
            self.rtnOrders(order)

    def parseOrder(self,order):
        logger.debug( '-parseOrder :%s' %order)

        self.orderMap[order['no']] = order
        if 'data' in order:
            self.orderMapDis[str(order['data']['entrustId'])] = order['no'] 

        if self.rtnOrder != None:
            self.rtnOrder(order)

    def close(self):
        self.api.close()

    def rtnOrder(self,o):
        pass

    def rspQueryOrders(self,o):
        pass

    def rspQueryOrder(self,o):
        pass

    def rtnTick(self,j):
        pass

    def rtnTrade(self,j):
        pass

