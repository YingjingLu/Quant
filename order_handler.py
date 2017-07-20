import multiprocessing as mp
import time
from constants import UTIL_CST, STK_CST
from trading_contracts import ContractCreateMethods as ct
from trading_orders import OrderCreateMethods as od
import pymongo
import datetime

FEE = 10
FILL_TIME_SECS = 10
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
                self.handle_order_feedback(order_feedback)


        self.join()

    def handle_order(self, order_dict):
        if order_dict["product_type"] == "STK":
            if order_dict["is_mkt_order"]:
                if order_dict["action"] == "SELL":
                    contract = ct.create_US_stock_contract(symbol = order_dict["symbol"])
                    order = od.MKT_order("SELL", order_dict["amount"])
                    self.send_order_to_app_q.put([order_dict["sell_order_id"], contract, order])
                    self.order_dict[order_dict["sell_order_id"]] = order_dict
                    self.order_dict[order_dict["sell_order_id"]]["last_avg_fill_price"] = 0
                    self.order_dict[order_dict["sell_order_id"]]["last_filled"] = 0
                    self.order_dict[order_dict["sell_order_id"]]["last_remaining"] = amount
                    self.order_dict[order_dict["sell_order_id"]]["order_place_dt"] = datetime.datetime.today()
            else: # if it is not market order
                if order_dict["action"] == "BUY":
                    contract = ct.create_US_stock_contract(stock_symbol = order_dict["symbol"])
                    amount = self.calc_amount_from_min_amount(order_dict["limit_price"])
                    order = od.LMT_order("BUY", amount, order_dict["limit_price"])
                    cancel_time = (datetime.datetime.today() + datetime.timedelta(seconds = FILL_TIME_SECS)).strftime("%Y%m%d %H:%M:%S")
                    order.conditionsCancelOrder = True
                    order.conditions.append(od.TimeCondition(cancel_time, True,False))
                    if amount != 0:
                        self.send_order_to_app_q.put([order_dict["order_id"], contract, order])
                        self.order_dict[order_dict["order_id"]] = order_dict
                        self.order_dict[order_dict["order_id"]]["last_avg_fill_price"] = order_dict["limit_price"]
                        self.order_dict[order_dict["order_id"]]["last_filled"] = amount
                        self.order_dict[order_dict["order_id"]]["last_remaining"] = 0
                        self.order_dict[order_dict["order_id"]]["order_place_dt"] = datetime.datetime.today()

                        # deduct cash
                        self.total_cash -= (order_dict["limit_price"]*amount + FEE)
                        self.send_order_to_app_q.put([order_dict["order_id"], contract, order])
                    else:
                        order_feedback = {
                                            "order_id": order_dict["order_id"],
                                            "contract": contract,
                                            "order": order,
                                            "order_status": "Canceled",
                                            "avg_fill_price": None,
                                            "order_state": None
                                        }
                        self.send_order_respond_q.put(order_feedback)


    def handle_order_feedback(self, order_feedback):
        # if successfully sold
        related_order = self.order_dict[order_feedback["order_id"]]
        if related_order['action'] == "SELL":
            if order_feedback["order_status"] == "Filled" or order_feedback["remaining"] == 0.0:
                send_order_feedback = {
                                    "order_id": order_feedback["order_id"],
                                    "order_status": "Filled",
                                    "avg_fill_price": order_feedback["avg_fill_price"],
                                    "amount": order_feedback["filled"],
                                    "action": "SELL"
                                }
                self.send_order_respond_q.put(send_order_feedback)
                self.total_cash -= FEE
            # if over time, record what we have since
            elif order_feedback["order_status"] == "Canceled" or order_feedback["order_status"] == "ApiCanceled":
                if order_feedback["filled"] > 0:
                    send_order_feedback = {
                                        "order_id": order_feedback["order_id"],
                                        "order_status": "Filled",
                                        "avg_fill_price": order_feedback["avg_fill_price"],
                                        "amount": order_feedback["filled"],
                                        "action": "SELL"
                                    }
                    self.send_order_respond_q.put(send_order_feedback)
                    self.total_cash -= FEE
            last_back_money = related_order["last_avg_fill_price"]*related_order["last_filled"]
            new_back_money = order_feedback["avg_fill_price"]*order_feedback["filled"] - last_back_money
            self.total_cash += new_back_money

        elif related_order['action'] == "BUY":
            if order_feedback["order_status"] == "Filled" or order_feedback["remaining"] == 0.0:
                send_order_feedback = {
                                    "order_id": order_feedback["order_id"],
                                    "order_status": "Filled",
                                    "avg_fill_price": order_feedback["avg_fill_price"],
                                    "amount": order_feedback["filled"],
                                    "action": "BUY"
                                }
                self.send_order_respond_q.put(send_order_feedback)
            # if over time, record what we have since
            elif order_feedback["order_status"] == "Canceled" or order_feedback["order_status"] == "ApiCanceled":
                if order_feedback["filled"] > 0:
                    send_order_feedback = {
                                        "order_id": order_feedback["order_id"],
                                        "order_status": "Filled",
                                        "avg_fill_price": order_feedback["avg_fill_price"],
                                        "amount": order_feedback["filled"],
                                        "action": "BUY"
                                    }
                    self.send_order_respond_q.put(send_order_feedback)
                    last_spend_money = related_order["last_avg_fill_price"]*related_order["last_filled"]
                    money_not_spend = last_spend_money -  order_feedback["avg_fill_price"]*order_feedback["filled"]
                    self.total_cash += new_back_money
                elif order_feedback["filled"] == 0:
                    send_order_feedback = {
                                        "order_id": order_feedback["order_id"],
                                        "order_status": "Canceled",
                                        "avg_fill_price": order_feedback["avg_fill_price"],
                                        "amount": order_feedback["filled"],
                                        "action": "BUY"
                                    }
                    self.send_order_respond_q.put(send_order_feedback)
                    self.total_cash += (FEE + related_order["last_avg_fill_price"]*related_order["last_filled"])

    def calc_amount_from_min_amount(self, price):
        amount = self.order_one_time_max / price // 100
        if amount == 0:
            return 0
        elif amount*price <= self.total_cash - FEE:
            return amount
        else:
            return 0

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
