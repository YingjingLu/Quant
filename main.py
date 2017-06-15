#################  Globals ############################
CONNECTION_IP = "127.0.0.1"
CONNECTION_PORT = 7497
CLIENT_ID = 999


############### End Globals ###############################


import sys
import argparse
import datetime
import collections
import inspect

import logging
import time
import os.path
import multiprocessing as mp


from ibapi import wrapper
from ibapi.client import EClient
from ibapi.utils import iswrapper

# types
from ibapi.common import *
from ibapi.order_condition import *
from ibapi.contract import *
from ibapi.order import *
from ibapi.order_state import *
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_report import CommissionReport
from ibapi.scanner import ScannerSubscription
from ibapi.ticktype import *

from ibapi.account_summary_tags import *


import pymongo
from pymongo import MongoClient


############### Import custom files ####################
from general_util import *
from ContractSamples import ContractSamples
from OrderSamples import OrderSamples
from AvailableAlgoParams import AvailableAlgoParams
from ScannerSubscriptionSamples import ScannerSubscriptionSamples
from FaAllocationSamples import FaAllocationSamples


from trading_contracts import ContractCreateMethods
from constants import *
from mongo_query_wrappers import *

############## End Importing Custom files ################

############### Debugging decorator func ######################
def print_func_when_executing(fn):
    def fn2(self):
        print(">>>  on: ", fn.__name__)
        fn(self)
        print(">>>  done: ", fn.__name__)
    return fn2
############## End debugging decorator func ###################



class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

        # initalize the TestClient test
        self.clntMeth2callCount = collections.defaultdict(int)
        self.clntMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nReq = collections.defaultdict(int)
        self.setupDetectReqId()

    def countReqId(self, methName, fn):
        def countReqId_(*args, **kwargs):
            self.clntMeth2callCount[methName] += 1
            idx = self.clntMeth2reqIdIdx[methName]
            if idx >= 0:
                sign = -1 if 'cancel' in methName else 1
                self.reqId2nReq[sign * args[idx]] += 1
            return fn(*args, **kwargs)

        return countReqId_

    def setupDetectReqId(self):

        methods = inspect.getmembers(EClient, inspect.isfunction)
        for (methName, meth) in methods:
            if methName != "send_msg":
                # don't screw up the nice automated logging in the send_msg()
                self.clntMeth2callCount[methName] = 0
                # logging.debug("meth %s", name)
                sig = inspect.signature(meth)
                for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                    (paramName, param) = pnameNparam
                    if paramName == "reqId":
                        self.clntMeth2reqIdIdx[methName] = idx

                setattr(TestClient, methName, self.countReqId(methName, meth))

# ! [ewrapperimpl]
class TestWrapper(wrapper.EWrapper):
    # ! [ewrapperimpl]
    def __init__(self):
        wrapper.EWrapper.__init__(self)

        self.wrapMeth2callCount = collections.defaultdict(int)
        self.wrapMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nAns = collections.defaultdict(int)
        self.setupDetectWrapperReqId()

    # TODO: see how to factor this out !!

    def countWrapReqId(self, methName, fn):
        def countWrapReqId_(*args, **kwargs):
            self.wrapMeth2callCount[methName] += 1
            idx = self.wrapMeth2reqIdIdx[methName]
            if idx >= 0:
                self.reqId2nAns[args[idx]] += 1
            return fn(*args, **kwargs)

        return countWrapReqId_

    def setupDetectWrapperReqId(self):

        methods = inspect.getmembers(wrapper.EWrapper, inspect.isfunction)
        for (methName, meth) in methods:
            self.wrapMeth2callCount[methName] = 0
            # logging.debug("meth %s", name)
            sig = inspect.signature(meth)
            for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                (paramName, param) = pnameNparam
                # we want to count the errors as 'error' not 'answer'
                if 'error' not in methName and paramName == "reqId":
                    self.wrapMeth2reqIdIdx[methName] = idx

            setattr(TestWrapper, methName, self.countWrapReqId(methName, meth))

class TradingApp(TestWrapper, TestClient):

    def __init__(self):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper = self)

        # init the socket
        self.nKeybInt = 0
        self.started = False
        self.nextValidOrderId = None
        self.permId2ord = {}
        self.reqId2nErr = collections.defaultdict(int)
        self.globalCancelOnly = False


    ##################### Togglers ###################################
        self.add_historical_data = 0
        self.query_dict = {}
        self.is_req_head_stamp = 1

    ###############      End togglers ############################
        self.db_client = MongoClient()
        if (self.is_req_head_stamp == 1):
            self.db = self.db_client.head_timestamp
            # reqId:{"stock": stk, "what_to_do": wtd}
            self.time_stamp_req_dict = dict()
            self.stk_timestamp_list = ["AMD", "FB", "AAPL", "AMZN", "NVDA", "BABA", "WB"]
            self.what_to_do_list = Query_CST.STK_HISTORY_WHAT_TO_DO_LIST


        self.count = 0

    def dumpTestCoverageSituation(self):
        for clntMeth in sorted(self.clntMeth2callCount.keys()):
            logging.debug("ClntMeth: %-30s %6d" % (clntMeth,
                                                   self.clntMeth2callCount[clntMeth]))

        for wrapMeth in sorted(self.wrapMeth2callCount.keys()):
            logging.debug("WrapMeth: %-30s %6d" % (wrapMeth,
                                                   self.wrapMeth2callCount[wrapMeth]))

    def dumpReqAnsErrSituation(self):
        logging.debug("%s\t%s\t%s\t%s" % ("ReqId", "#Req", "#Ans", "#Err"))
        for reqId in sorted(self.reqId2nReq.keys()):
            nReq = self.reqId2nReq.get(reqId, 0)
            nAns = self.reqId2nAns.get(reqId, 0)
            nErr = self.reqId2nErr.get(reqId, 0)
            logging.debug("%d\t%d\t%s\t%d" % (reqId, nReq, nAns, nErr))

    # ! [connectack]
    def connectAck(self):
        if self.async:
            self.startApi()


    def historicalDataRequests_req(self):
        # Requesting historical data
        # ! [reqHeadTimeStamp]
        #self.reqHeadTimeStamp(4103, ContractSamples.USStockAtSmart(), "TRADES", 0, 1)
        # ! [reqHeadTimeStamp]
        # ! [reqhistoricaldata]
        # queryTime = (datetime.datetime.today() -
        #              datetime.timedelta(days=180)).strftime("%Y%m%d %H:%M:%S")
        queryTime = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")
        # String queryTime = DateTime.Now.AddMonths(-6).ToString("yyyyMMdd HH:mm:ss")
        # self.reqHistoricalData(4101, ContractSamples.USStockAtSmart(), queryTime,
        #                        "1 M", "1 day", "TRADES", 1, 1, [])
        contract = ContractCreateMethods.create_US_stock_contract("AMD", "STK")
        self.reqHistoricalData(4101, contract, queryTime,
                               "5 Y", "30 mins", "TRADES", 1, 1, [])

    def historicalDataRequests_cancel(self):
        # Canceling historical data requests
        self.cancelHistoricalData(4101)

    def historicalData(self, reqId: TickerId, date: str, _open: float, high: float,
                       low: float, close: float, volume: int, barCount: int,
                       WAP: float, hasGaps: int):
        super().historicalData(reqId, date, _open, high, low, close, volume,
                               barCount, WAP, hasGaps)
        mongo_insert_historical(self.collection, date, _open, high, low, close, volume, barCount, WAP, hasGaps)

        self.count += 1
        if self.count % 14 == 0:
            print ("1 day finished\n")

        if (yr == 2017 and mo == 6 and dy == 2):
            print("finished !!!!!!!!")
            self.stop()

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd ", reqId, "from", start, "to", end)



    #>>>>>>>>>>>>>>>>>>>>>> NKT Data L2
    def marketDepthOperations_req(self):
        # Requesting the Deep Book
        # ! [reqmarketdepth]
        self.reqMktDepth(2101, ContractSamples.USStock(), 5, [])
        # ! [reqmarketdepth]

        # Request list of exchanges sending market depth to UpdateMktDepthL2()
        # ! [reqMktDepthExchanges]
        self.reqMktDepthExchanges()

    def updateMktDepth(self, reqId: TickerId, position: int, operation: int,
                       side: int, price: float, size: int):
        super().updateMktDepth(reqId, position, operation, side, price, size)
        print("UpdateMarketDepth. ", reqId, "Position:", position, "Operation:",
              operation, "Side:", side, "Price:", price, "Size", size, "time", datetime.datetime.now())

    def updateMktDepthL2(self, reqId: TickerId, position: int, marketMaker: str,
                         operation: int, side: int, price: float, size: int):
        super().updateMktDepthL2(reqId, position, marketMaker, operation, side,
                                 price, size)
        print("UpdateMarketDepthL2. ", reqId, "Position:", position, "Operation:",
              operation, "Side:", side, "Price:", price, "Size", size,  "time", datetime.datetime.now())

    def marketDepthOperations_cancel(self):
        # Canceling the Deep Book request
        # ! [cancelmktdepth]
        self.cancelMktDepth(2101)

    def realTimeBars_req(self):
        # Requesting real time bars
        # ! [reqrealtimebars]
        self.reqRealTimeBars(3101, ContractSamples.USStockAtSmart(), 5, "TRADES", True, [])

    def realtimeBar(self, reqId: TickerId, time: int, open: float, high: float,
                    low: float, close: float, volume: int, wap: float,
                    count: int):
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        print("RealTimeBars. ", reqId, "Time:", time, "Open:", open,
              "High:", high, "Low:", low, "Close:", close, "Volume:", volume,
              "Count:", count, "WAP:", wap,  "time", datetime.datetime.now())

    def headTimeStamp_req_wrapper(self):
        ticket_start = Query_CST.HEAD_TIMESTAMP_1
        for stk in self.stk_timestamp_list:
            for wtd in self.what_to_do_list:
                self.time_stamp_req_dict[ticket_start] = {"stock": stk, "what_to_do": wtd}
                self.headTimeStamp_req(ticket_start,
                                       ContractCreateMethods.create_US_stock_contract(stock_symbol = stk),
                                       wtd)
                ticket_start += 1
                time.sleep(1)



    def headTimeStamp_req(self, tick_id, contract, what_to_do):
        self.reqHeadTimeStamp(tick_id, contract, what_to_do, 0, 1)

    def headTimestamp(self, reqId:int, headTimestamp:str):
        post = {self.time_stamp_req_dict[reqId]["what_to_do"]: parse_datetime(headTimestamp)}
        print("post: ", post)
        self.db[self.time_stamp_req_dict[reqId]["stock"]].insert_one(post)
        print("------ Canceled --------")

    def realTimeBars_cancel(self):
        # Canceling real time bars
        # ! [cancelrealtimebars]
        self.cancelRealTimeBars(3101)

    def tickDataOperations_req(self):
        self.reqMktData(1101, ContractSamples.USStockAtSmart(), "", False, False, [])

    def tickDataOperations_cancel(self):
        # Canceling the market data subscription
        # ! [cancelmktdata]
        self.cancelMktData(1101)

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float,
                  attrib: TickAttrib):
        super().tickPrice(reqId, tickType, price, attrib)
        print("Tick Price. Ticker Id:", reqId, "tickType:", tickType, "Price:",
              price, "CanAutoExecute:", attrib.canAutoExecute,
              "PastLimit", attrib.pastLimit)

    # ! [tickprice]
    # ! [ticksize]
    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        super().tickSize(reqId, tickType, size)
        print("Tick Size. Ticker Id:", reqId, "tickType:", tickType, "Size:", size)

    # ! [ticksize]

    # ! [tickgeneric]
    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        super().tickGeneric(reqId, tickType, value)
        print("Tick Generic. Ticker Id:", reqId, "tickType:", tickType, "Value:", value)

    # ! [tickgeneric]

    # ! [tickstring]
    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        super().tickString(reqId, tickType, value)
        print("Tick string. Ticker Id:", reqId, "Type:", tickType, "Value:", value)

    def keyboardInterrupt(self):
        self.nKeybInt += 1
        if self.nKeybInt == 1:
            self.stop()
        else:
            print("Finishing test")
            self.done = True

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)

        logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        # ! [nextvalidid]

        # we can start now
        self.start()


    def start(self):
        if self.started:
            return

        self.started = True
        if self.globalCancelOnly:
            print("Executing GlobalCancel only")
            self.reqGlobalCancel()
        else:
            print("Executing requests")
            self.reqGlobalCancel()
            if self.add_historical_data:
                self.historicalDataRequests_req()
            elif self.is_req_head_stamp:
                self.headTimeStamp_req_wrapper()
            else:
                self.marketDepthOperations_req()
            #self.tickDataOperations_req()
                self.realTimeBars_req()


    def stop(self):
        if self.add_historical_data:
            self.historicalDataRequests_cancel()
        #self.tickDataOperations_cancel()
        else:

            self.realTimeBars_cancel()
            self.marketDepthOperations_cancel()
        self.db_client.close()
        print("executing cancel finished")

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid





def main():
    app = TradingApp()

    app.connect(CONNECTION_IP, CONNECTION_PORT, CLIENT_ID)

    app.run()

if __name__ == "__main__":
    main()
