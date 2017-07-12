import multiprocessing as mp
import time
from constants import UTIL_CST, STK_CST
from trading_contracts import ContractCreateMethods as ct
from trading_orders import OrderCreateMethods as od
import pymongo

class OrderHandler(mp.Process):

    def __init__(self, total_cash, send_order_to_app_q, OH_recv_order_q, recv_order_feedback_q, OH_send_order_respond_q ):
        super().__init__(target = self.reader, args = ())
        self.send_order_to_app_q = send_order_to_app_q
        #self.db_client = pymongo.MongoClient()
        # get the account balance
        self.recv_order_q = OH_recv_order_q
        self.recv_order_feedback_q = recv_order_feedback_q
        self.send_order_respond_q  = OH_send_order_respond_q
        self.total_cash = total_cash
        self.order_one_time_max = self.calc_one_time_order_amount()
        # get previous stock price
        # calculate the amount per order

        self.order_dict = dict()
        self.order_wait_time = 3


    def reader(self):
        while True:
            if not self.recv_order_q.empty():
                order = self.recv_order_q.get(block=False)
                if order == 0:
                    break
                else:
                    self.handle_order(order)
            if not  self.recv_order_feedback_q.empty():
                order_feedback = self.recv_order_feedback_q.get()
                self.send_order_respond_q.put(order_feedback)

        self.join()

    def handle_order(self, order_dict):
        if order_dict["product_type"] == "STK":
            if order_dict["is_mkt_order"]:
                if order_dict["action"] == "SELL":
                    contract = ct.create_US_stock_contract(symbol = order_dict["symbol"])
                    order = od.MKT_order("SELL", order_dict["amount"])
                    self.send_order_to_app_q.put([order_dict["sell_order_id"], contract, order])
            else: # if it is not market order
                if order_dict["action"] == "BUY":
                    contract = ct.create_US_stock_contract(symbol = order_dict["symbol"])
                    amount = self.calc_amount_from_min_amount(order_dict["limit_price"])
                    order = od.LMT_order("BUY", amount)
                    cancel_time = (datetime.datetime.today() + datetime.timedelta(seconds = 5)).strftime("%Y%m%d %H:%M:%S")
                    order.conditionsCancelOrder = True
                    order.conditions.append(od.TimeCondition(cancel_time, True,False))
                    self.send_order_to_app_q.put([order_dict["order_id"], contract, order])



    def calc_amount_from_min_amount(self, price):
        return self.order_one_time_max / price // 100

    def calc_one_time_order_amount(self):
        if self.total_cash<= 3000:
            return self.total_cash
        if self.total_cash <= 10000:
            return 3000

        elif self.total_cash <= 40000:
            return 5000
        else:
            return 8000

    def call_the_day(self):
        # when a day is going to end, sell all existing order
        ##
        ## needs CONSTRUCTION
        ##
        pass
