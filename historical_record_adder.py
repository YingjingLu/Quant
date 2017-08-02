#################  Globals ############################
CONNECTION_IP = "127.0.0.1"
CONNECTION_PORT = 7497
CLIENT_ID = 0


############### End Globals ###############################


import sys
import argparse
import datetime
import collections
import inspect
import threading
import pprint

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
from mongo_build_wrapper import *

from stock_analysis import *
from order_handler import *



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
        self.add_historical_data = 1
        self.from_start = 0
        self.populate_rest_TRADES = 0
        self.query_dict = {}
        self.is_req_head_stamp = 0
        self.is_req_realtime_mktdepth = 0

    ###############      End togglers ############################
        self.db_client = MongoClient()
        if (self.is_req_head_stamp == 1):
            self.db = self.db_client.head_timestamp
            # reqId:{"stock": stk, "what_to_do": wtd}
            self.time_stamp_req_dict = dict()
            self.stk_timestamp_list = ["AMD", "FB", "AAPL", "AMZN", "NVDA", "BABA", "WB"]
            self.what_to_do_list = QUERY_CST.STK_HISTORY_WHAT_TO_DO_LIST

        elif(self.add_historical_data == 1):
            # reqId:{"symbol": symbol, "what_to_do": wtd, "bar_size": bar_size, "start_dt":start_dt, "end_dt": end_dt, "first_time": 0/1, "db":db, "collection": collection}
            self.historical_data_req_dict = dict()
            #
            self.stk_historical_list = [{"symbol": "NVDA", "start_dt": datetime.datetime(2017, 7, 3, 0, 0, 0), "end_dt": datetime.datetime(2017, 7, 3, 23, 59, 59), "what_to_do": "TRADES", "first_time": 0},
                                        {"symbol": "NVDA", "start_dt": datetime.datetime(2017, 7, 14, 0, 0, 0), "end_dt": datetime.datetime(2017, 7, 14, 23, 59, 59), "what_to_do": "TRADES", "first_time": 0}
                                        ]
            self.what_to_do_list = QUERY_CST.STK_HISTORY_WHAT_TO_DO_LIST


        self.req_count = 0
        self.line_count = 0
        self.log_file = open("log.txt", "a")

        ################### Communication queues ##########################
        self.rt_bar_req_dict = {3101: "AMD"}

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

    #######################  Requesting Order Info End ###################################

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
                if self.from_start == 1:
                    self.historicalDataRequests_req_wrapper()
                elif self.from_start == 0:
                    self.historicalDataRequests_continue_req_wrapper()
                else:
                    if self.populate_rest_TRADES == 1:
                        self.populate_stk_trades_in_list()
            elif self.is_req_head_stamp:
                self.headTimeStamp_req_wrapper()
            else:
                #self.marketDepthOperations_req()
                #self.tickDataOperations_req()
                self.realTimeBars_req()
                self.orderOperations_req()


    def stop(self):
        if self.add_historical_data:
            self.tickDataOperations_cancel()
        else:

            self.realTimeBars_cancel()
            self.marketDepthOperations_cancel()
        self.log_file.close()
        self.db_client.close()
        print("executing cancel finished")

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    def historicalDataRequests_continue_req_wrapper(self):
        reqId = QUERY_CST.HISTORY_REQ_1
        bar_size = "5 secs"
        print(">>> Enter continue")
        for item_dict in self.stk_historical_list:
            symbol = item_dict["symbol"]
            first_time = item_dict["first_time"]
            end_dt = item_dict["end_dt"]
            start_dt = item_dict["start_dt"]
            what_to_do = item_dict["what_to_do"]
            self.historical_data_req_dict[reqId] = {
                                                    "symbol": symbol,
                                                    "what_to_do": what_to_do,
                                                    "bar_size": bar_size,
                                                    "start_dt":start_dt,
                                                    "end_dt": end_dt,
                                                    "first_time": first_time,
                                                    "db": self.db_client[symbol_to_db_name(symbol)],
                                                    "collection": self.db_client[symbol_to_db_name(symbol)][convert_collection_name(what_to_do, bar_size)],
                                                    "last_start":  datetime.datetime.today(),
                                                    "start_toggle": True
                                                    }
            reqId += 1
        for _id in self.historical_data_req_dict.keys():
            print(_id)
            pprint.pprint(self.historical_data_req_dict[_id])
        for reqId, query_dict in self.historical_data_req_dict.items():
            self.historicalDataRequests_req(query_dict["end_dt"], reqId)
            time.sleep(0.4)
            if self.req_count >= 59:
                time.sleep(600)
    def historicalDataRequests_req(self, end_dt, reqId):
        start_dt = self.historical_data_req_dict[reqId]["start_dt"]
        if end_dt <= start_dt:
            print("Completed Historical Req: ", self.historical_data_req_dict[reqId])
            del self.historical_data_req_dict[reqId]
            return
        if self.req_count >= 59:
            print(">>> 60 Req, wait")
            time.sleep(482)
            print(">>> Finish Waiting")
            self.req_count = 0
        self.req_count += 1

        symbol = self.historical_data_req_dict[reqId]["symbol"]
        what_to_do = self.historical_data_req_dict[reqId]["what_to_do"]
        bar_size = self.historical_data_req_dict[reqId]["bar_size"]
        step_size = bar_size_to_step_size(bar_size)
        if end_dt <= start_dt:
            print("Completed Historical Req: ", self.historical_data_req_dict[reqId])
            del self.historical_data_req_dict[reqId]
            return
        # Requesting historical data
        # ! [reqHeadTimeStamp]
        #self.reqHeadTimeStamp(4103, ContractSamples.USStockAtSmart(), "TRADES", 0, 1)
        # ! [reqHeadTimeStamp]
        # ! [reqhistoricaldata]
        # queryTime = (datetime.datetime.today() -
        #              datetime.timedelta(days=180)).strftime("%Y%m%d %H:%M:%S")
        #queryTime = (datetime.datetime.today()-datetime.timedelta(days=4)).strftime("%Y%m%d %H:%M:%S")
        queryTime = end_dt.strftime("%Y%m%d %H:%M:%S")
        # String queryTime = DateTime.Now.AddMonths(-6).ToString("yyyyMMdd HH:mm:ss")
        # self.reqHistoricalData(4101, ContractSamples.USStockAtSmart(), queryTime,
        #                        "1 M", "1 day", "TRADES", 1, 1, [])
        contract = ContractCreateMethods.create_US_stock_contract(symbol)
        self.reqHistoricalData(reqId, contract, queryTime,
                               step_size, bar_size, what_to_do, 1, 1, [])
        print(">>> Req Count: ", self.req_count, " Req Sent")
    def historicalDataRequests_cancel(self, reqId):
        # Canceling historical data requests
        self.cancelHistoricalData(reqId)

    def historicalData(self, reqId: TickerId, date: str, _open: float, high: float,
                       low: float, close: float, volume: int, barCount: int,
                       WAP: float, hasGaps: int):
        super().historicalData(reqId, date, _open, high, low, close, volume,
                               barCount, WAP, hasGaps)

        if mongo_insert_historical(self.historical_data_req_dict[reqId]["collection"],
                                self.historical_data_req_dict[reqId],
                                date,
                                _open,
                                high,
                                low,
                                close,
                                volume,
                                barCount,
                                WAP,
                                hasGaps):

            self.line_count += 1
        if self.historical_data_req_dict[reqId]["first_time"] == 1:
            self.historical_data_req_dict[reqId]["collection"].create_index([("datetime", pymongo.DESCENDING)],unique = True)
            self.historical_data_req_dict[reqId]["first_time"] = 0

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd ", reqId, "from", start, "to", end)
        print(">>> self.req_count: ", self.req_count)

        new_dt = self.historical_data_req_dict[reqId]["last_start"]
        self.historical_data_req_dict[reqId]["start_toggle"] = True
        self.historicalDataRequests_cancel(reqId)
        if self.line_count == 720:
            self.log_file.write("Success: "+ self.historical_data_req_dict[reqId]["symbol"] + "from " + start + "to " + end+ "\n")
        else:
            self.log_file.write("Fail: "+ self.historical_data_req_dict[reqId]["symbol"] + "from " + start + "to " + end+ "\n")
        print(">>> Line Count: ", self.line_count)
        time.sleep(2)
        self.line_count = 0
        self.historicalDataRequests_req(new_dt, reqId)
def main():
    app = TradingApp()
    app.connect(CONNECTION_IP, CONNECTION_PORT, CLIENT_ID)

    app.run()

if __name__ == "__main__":
    main()
