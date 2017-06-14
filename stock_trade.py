import multiprocessing as mp
import time
from constants import UTIL_CST, STK_CST
from trading_contracts import ContractCreateMethods as ct
from trading_orders import OrderCreateMethods as od

# messge format {price:3, volumn: 8}

class StockTrade(object):

    def __init__(self, app, db, tick_id, symbol, msg_queue, max_cash, shares_holding):
        self.app = app
        self.db = db
        self.tick_id = tick_id
        self.symbol = symbol
        self.msg_queue = msg_queue
        self.max_cash = max_cash
        self.shares_holding = shares_holding
        self.cur_collection = self.db.TRADES_30sec

    def reader(self):
        while True:
            msg = self.msg_queue.get()
            if(msg == MKT_CLOSE):
                break

    def place_order(self, action, price, quantity):
        if action == STK_CST.BUY:
            order_action = "BUY"

        elif action == STK.SELL:
            order_action = "SELL"
        if price == None:
            self.placeOrder(self.app.nextOrderId(), ct.create_US_stock_contract(stock_symbol = self.symbol),
                            od.MKT_order(order_action, quantity))
        else:
            self.placeOrder(self.app.nextOrderId(), ct.create_US_stock_contract(stock_symbol = self.symbol),
                            od.LMT_order(order_action, quantity, price))

        self.max_cash -= price * quantity
        self.shares_holding += action * quantity


    def cancel_order(self, position):
        pass
