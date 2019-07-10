# encoding: UTF-8

import hashlib
import zlib
import json
import uuid

from time import sleep
from threading import Thread

import websocket    
import urllib2, hashlib,struct,sha,time
import traceback

import logging

zb_usd_url = "wss://api.zb.com:9999/websocket"

logger = logging.getLogger()
logger.setLevel(logging.INFO) 

ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)   # 输出到console的log等级的开关
 
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)




class ZB_Sub_Spot_Api(object):
    """基于Websocket的API对象"""
    def __init__(self,apiKey , secretKey,onMessage = None):
        """Constructor"""
        self.apiKey =  apiKey       # 用户名
        self.secretKey = secretKey     # 密码

        self.ws_sub_spot = None          # websocket应用对象  现货对象
        self.connect_Subpot()
        self.connectd = False

        self.handle = onMessage
        self.onOpenProcess = None

    #----------------------------------------------------------------------
    def reconnect(self):
        """重新连接"""
        # 首先关闭之前的连接
        try:
            self.close()
        except Exception, e:
            logger.exception('exception') 

        
        # 再执行重连任务
        self.ws_sub_spot = websocket.WebSocketApp(self.host, 
                                         on_message=self.onMessage,
                                         on_error=self.onError,
                                         on_close=self.onClose,
                                         on_open=self.onOpen)        
    
        self.thread = Thread(target=self.ws_sub_spot.run_forever)
        self.thread.start()
    
    #----------------------------------------------------------------------
    def connect_Subpot(self):
        self.host = zb_usd_url
#        self.apiKey = apiKey
#        self.secretKey = secretKey

#        websocket.enableTrace(trace)
#        websocket.enableTrace(True)
  

        self.ws_sub_spot = websocket.WebSocketApp(self.host, 
                                             on_message=self.onMessage,
                                             on_error=self.onError,
                                             on_close=self.onClose,
                                             on_open=self.onOpen)        
            
        self.thread = Thread(target=self.ws_sub_spot.run_forever)
        self.thread.start()

    #----------------------------------------------------------------------
    def readData(self, evt):
        """解压缩推送收到的数据"""
        # # 创建解压器
        # decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        
        # # 将原始数据解压成字符串
        # inflated = decompress.decompress(evt) + decompress.flush()
        
        # 通过json解析字符串
        data = json.loads(evt)
        
        return data

    #----------------------------------------------------------------------
    def close(self):
        """关闭接口"""
        if self.thread and self.thread.isAlive():
            self.ws_sub_spot.close()
            self.thread.join()

    #----------------------------------------------------------------------
    def onMessage(self, ws, evt):
        """信息推送""" 
        try:
            if self.handle != None:
                self.handle(evt)
        except Exception, e:
            logger.exception('exception') 
        
    #----------------------------------------------------------------------
    def onError(self, ws, evt):
        """错误推送"""
        self.reconnect()
        
    #----------------------------------------------------------------------
    def onClose(self, ws):
        self.connectd = False
        """接口断开"""
        
    #----------------------------------------------------------------------
    def onOpen(self, ws):
        self.connectd = True
        """接口打开"""
        if self.onOpenProcess != None:
            self.onOpenProcess()

    #----------------------------------------------------------------------
    def subscribeSpotTicker(self, symbol_pair):
        # 现货的 ticker
        symbol_pair = symbol_pair.replace('_','')
        req = "{'event':'addChannel','channel':'%s_ticker'}" % symbol_pair
        self.ws_sub_spot.send(req)

    #----------------------------------------------------------------------
    def subscribeSpotDepth(self, symbol_pair):
        # 现货的 市场深度
        symbol_pair = symbol_pair.replace('_','')
        req = "{'event':'addChannel','channel':'%s_depth'}" % symbol_pair
        self.ws_sub_spot.send(req)

    #----------------------------------------------------------------------
    def subscribeSpotMarkets(self):
        # 现货的 市场深度
        req = "{'event':'addChannel','channel':'markets'}"
        self.ws_sub_spot.send(req)

    #----------------------------------------------------------------------
    def subscribeSpotTrades(self, symbol_pair):
        symbol_pair = symbol_pair.replace('_','')
        req = "{'event':'addChannel','channel':'%s_trades'}" % symbol_pair
        self.ws_sub_spot.send(req)

    #----------------------------------------------------------------------
    def __fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize
    #----------------------------------------------------------------------
    def __doXOr(self, s, value):
        slist = list(s)
        for index in xrange(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)
    #----------------------------------------------------------------------
    def __hmacSign(self, aValue, aKey):
        keyb   = struct.pack("%ds" % len(aKey), aKey)
        value  = struct.pack("%ds" % len(aValue), aValue)
        k_ipad = self.__doXOr(keyb, 0x36)
        k_opad = self.__doXOr(keyb, 0x5c)
        k_ipad = self.__fill(k_ipad, 64, 54)
        k_opad = self.__fill(k_opad, 64, 92)
        m = hashlib.md5()
        m.update(k_ipad)
        m.update(value)
        dg = m.digest()
        
        m = hashlib.md5()
        m.update(k_opad)
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

    #----------------------------------------------------------------------
    def __digest(self, aValue):
        value  = struct.pack("%ds" % len(aValue), aValue)
        h = sha.new()
        h.update(value)
        dg = h.hexdigest()
        return dg

    #----------------------------------------------------------------------
    def generateSign(self, params):
        """生成签名"""
        '''
        {"accesskey":"0f39fb8b-d95d-4afe-b2a9-94f5f4d9fdb5","channel":"getaccountinfo","event":"addChannel"}
        '''
        l = []
        for key in sorted(params.keys()):
            l.append('"%s":"%s"' %(key, params[key]))
        sign = ','.join(l)
        sign = str('{' + sign + '}')

        SHA_secret = self.__digest(self.secretKey)
        return self.__hmacSign( sign, SHA_secret)
        # return hashlib.md5(sign.encode('utf-8')).hexdigest().upper()

    #----------------------------------------------------------------------
    def sendTradingRequest(self, channel, params):
        """发送交易请求"""
        # 在参数字典中加上api_key和签名字段
        params['accesskey'] = self.apiKey
        params['channel'] = channel
        params['event'] = "addChannel"

        params['sign'] = self.generateSign(params)
        
        # 使用json打包并发送
        j = json.dumps(params)
        
        # 若触发异常则重连
        try:
            self.ws_sub_spot.send(j)
        except websocket.WebSocketConnectionClosedException:
            pass 

    #----------------------------------------------------------------------
    def order(self, symbol_pair, type_, price, amount):
        """现货委托"""
        symbol_pair = symbol_pair.replace('_','') 
        params = {}
        params['tradeType'] = '1' if str(type_) == 'B' else '0'
        params['price'] = str(price)
        params['amount'] = str(amount)
        params['no'] = str(type_) + "_" + str(uuid.uuid4())
        
        channel = symbol_pair.lower() + "_order"
        
        self.sendTradingRequest(channel, params)
        return params['no'] 

    #----------------------------------------------------------------------
    def cancel(self, symbol_pair, orderid):
        """现货撤单"""
        symbol_pair = symbol_pair.replace('_','') 
        params = {}
        params['id'] = str(orderid)
        params['no'] = "C_" + str(uuid.uuid4()) + "_" + str(orderid)
        
        channel = symbol_pair.lower() + "_cancelorder" 


        
        self.sendTradingRequest(channel, params)
        return params['no'] 
       
    
    #----------------------------------------------------------------------
    def trans(self,userFrom,userTo,coins,amount):
        channel = 'doTransferFunds'
        params = {}
        params['amount'] = str(amount)
        params['currency'] = coins
        params['fromUserName'] = userFrom
        params['toUserName'] = userTo
        self.sendTradingRequest(channel, params)

    def spotUserInfo(self):
        """查询现货账户"""
        channel = 'getaccountinfo'
        self.sendTradingRequest(channel, {})

    def ping(self):
        """查询现货账户"""
        channel = 'getRepayments'
        self.sendTradingRequest(channel, {})

    #----------------------------------------------------------------------
    def getOrder(self, symbol_pair, orderid):
        """查询现货委托信息"""
        symbol_pair = symbol_pair.replace('_','') 
        params = {}
        params['id'] = str(orderid)
        
        channel = symbol_pair.lower() + "_getorder"
        
        self.sendTradingRequest(channel, params)
        return True

    def getOrders(self, symbol_pair):
        """查询现货委托信息"""
        symbol_pair = symbol_pair.replace('_','') 
        params = {}
        params['pageIndex'] = "1"
        params['pageSize'] = "50"
        
        channel = symbol_pair.lower() + "_getordersignoretradetype"
        
        self.sendTradingRequest(channel, params)
        return True

    #----------------------------------------------------------------------
    def spotGetOrders(self, symbol_pair , orderid):
        pass
