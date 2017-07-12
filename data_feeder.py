
from stock_analysis import *
from order_handler import *

class DataFeeder(object):

    def __init__(self, symbol):
        self.send_rt_bar_q = mp.Queue()
        self.send_order_feedback_q = mp.Queue()
        self.symbol = symbol
        self.time_int = 0

        self.db_client = pymongo.MongoClient()
        self.db_name = symbol_to_db_name(self.symbol)
        self.db = self.db_client[self.db_name]

        self.rt_bar_start_time = 0

    def set_test_time_frame(self, start_dt, end_dt):
        self.start_dt = start_dt
        self.end_dt = end_dt

    def set_test_bar_size(self, bar_size):
        self.rt_bar_size = bar_size

    def query_base_data(self):
        self.cursor_list = list(self.db[convert_collection_name("TRADES", self.rt_bar_size)].find({"datetime": {"$gte": self.start_dt, "$lte": self.end_dt}}).sort("datetime", pymongo.ASCENDING))

    def start_feeding(self):
        for record_dict in self.cursor:
            record_dict["time"] = self.rt_bar_start_time
            self.rt_bar_start_time += QUERY_CST[self.rt_bar_size]
            self.send_rt_bar_q.put(record_dict)
        print("Finish putting records from %s to %s" % (str(self.start_dt), str(self,end_dt)))

    def order_feedback_worker(self):
        pass

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

    OH = OrderHandler(DF, 250000, DF.send_order_feedback_q)
    SA = StockAnalysis(DF, "AMD", DF.send_rt_bar_q,
                       rt_price_q, OH.recv_order_q,
                       OH.send_order_respond_q, send_log_q)


if __name__ == "__main__":
    main()
