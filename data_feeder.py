
from stock_analysis import *
from order_handler import *
import time
import datetime

CUR_STK_PRICE = 0
class DataFeeder(object):

    def __init__(self, symbol):
        self.send_rt_bar_q = mp.Queue()
        self.send_order_feedback_q = mp.Queue()
        self.order_recv_q = mp.Queue()
        self.symbol = symbol
        self.time_int = 0

        self.rt_bar_start_time = 0

    def set_test_time_frame(self, start_dt, end_dt):
        self.start_dt = start_dt
        self.end_dt = end_dt

    def set_test_bar_size(self, bar_size):
        self.rt_bar_size = bar_size

    def start_feeding(self):
        global CUR_STK_PRICE
        self.db_client = pymongo.MongoClient()
        self.db_name = symbol_to_db_name(self.symbol)
        self.db = self.db_client[self.db_name]
        self.db[convert_RT_collection_name("5 secs")].delete_many({})
        self.db[convert_RT_collection_name("1 min")].delete_many({})
        cursor_list = list(self.db[convert_collection_name("TRADES", self.rt_bar_size)].find({"datetime": {"$gte": self.start_dt, "$lte": self.end_dt}}).sort("datetime", pymongo.ASCENDING))
        for record_dict in cursor_list:
            record_dict["time"] = self.rt_bar_start_time
            self.rt_bar_start_time += QUERY_CST.RT_BAR_BAR_SIZE_TO_SEC[self.rt_bar_size]
            self.send_rt_bar_q.put(record_dict)
            CUR_STK_PRICE = record_dict["close"]
            time.sleep(0.1)
        print("Finish putting records from %s to %s" % (str(self.start_dt), str(self.end_dt)))

    def order_feedback_worker(self):
        while True:
            global CUR_STK_PRICE
            order_req_list = self.order_recv_q.get()
            if order_req_list[2].action == "BUY":
                self.send_order_feedback_q.put(
                                                {
                                                "order_id": order_req_list[0],
                                                "order_status": "Filled",
                                                "filled": order_req_list[2].totalQuantity,
                                                "remaining": 0,
                                                "avg_fill_price": order_req_list[2].lmtPrice,
                                                "perm_id": None,
                                                "parent_id": None,
                                                "cur_time": datetime.datetime.today()
                                                }
                )
            elif order_req_list[2].action == "SELL":
                self.send_order_feedback_q.put(
                                                {
                                                "order_id": order_req_list[0],
                                                "order_status": "Filled",
                                                "filled": order_req_list[2].totalQuantity,
                                                "remaining": 0,
                                                "avg_fill_price": CUR_STK_PRICE,
                                                "perm_id": None,
                                                "parent_id": None,
                                                "cur_time": datetime.datetime.today()
                                                }
                )

    def send_rt_bar_worker(self):
        self.start_feeding()

    def placeOrder(self, order_dict, contract, order):
        self.send_order_feedback_q.put({
                                            "order_id": order_dict["order_id"],
                                            "contract": contract,
                                            "order": order,
                                            "order_status": "Filled",
                                            "avg_fill_price": None,
                                            "order_state": orderState
            })

    def start(self):
        self.rt_send_p = mp.Process(target = self.send_rt_bar_worker, args=())
        self.feedback_send_p = mp.Process(target = self.order_feedback_worker, args = ())
        self.feedback_send_p.start()
        self.rt_send_p.start()
        self.rt_send_p.join()
        self.feedback_send_p.join()
        print("Data Feed Done ......")



def main():
    rt_price_q = mp.Queue()
    send_log_q = mp.Queue()
    DF = DataFeeder("AMD")
    DF.set_test_bar_size("5 secs")
    DF.set_test_time_frame(datetime.datetime(2017, 7, 17, 0, 0, 0),
                           datetime.datetime(2017, 7, 17, 23, 59, 59))

    rt_price_q = mp.Queue()
    send_log_q = mp.Queue()
    oh_send_order_to_app_q = DF.order_recv_q
    app_send_order_feedback_to_oh_q = DF.send_order_feedback_q
    app_send_rt_bar_to_sa_q = DF.send_rt_bar_q

    sa_send_order_to_oh_q = mp.Queue()
    oh_send_order_feedback_to_sa_q = mp.Queue()

    OH = OrderHandler(230000,oh_send_order_to_app_q, sa_send_order_to_oh_q, app_send_order_feedback_to_oh_q, oh_send_order_feedback_to_sa_q)
    SA = StockAnalysis("AMD", app_send_rt_bar_to_sa_q,
                       rt_price_q,sa_send_order_to_oh_q,
                       oh_send_order_feedback_to_sa_q, send_log_q)
    OH.start()
    SA.start()
    DF.start()


if __name__ == "__main__":
    main()
