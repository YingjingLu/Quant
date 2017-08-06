import multiprocessing as mp
import time
from constants import UTIL_CST, STK_CST
import pymongo
import datetime

class MarketDepth2Bar(mp.Process):
    def __init__(self, mkt_data_req_dict, mkt_depth_recv_q,rt_bar_output_q_dict):
        super().__init__(target = self.reader, args = ())
        self.mkt_data_stat_dict = dict()
        # req_id: {"symbol": symbol, "last_start": last_start, "output_q": output_q}
        self.mkt_data_req_dict = dict()
        for req_id, symbol in mkt_data_req_dict.items():
            self.mkt_data_req_dict[req_id] = dict()
            self.mkt_data_req_dict[req_id]["symbol"] = symbol
            self.mkt_data_req_dict[req_id]["last_price"] = -1
            if self.mkt_data_stat_dict.get(symbol) == None:
                self.mkt_data_stat_dict[symbol] = dict()
                self.mkt_data_stat_dict[symbol]["high"] = -1
                self.mkt_data_stat_dict[symbol]["volume"] = 0
                self.mkt_data_stat_dict[symbol]["WAP"] = 0
                self.mkt_data_stat_dict[symbol]["low"] = -1
                self.mkt_data_stat_dict[symbol]["open"] = -1
                self.mkt_data_stat_dict[symbol]["close"] = -1
                self.mkt_data_stat_dict[symbol]["time"] = -1
                self.mkt_data_stat_dict[symbol]["datetime"] = -1
                self.mkt_data_stat_dict[symbol]["cur_price"] = -1
                self.mkt_data_stat_dict[symbol]["count"] = 0

        for symbol, q in rt_bar_output_q_dict.items():
            self.mkt_data_stat_dict[symbol]["output_q"] = rt_bar_output_q_dict[symbol]

        self.mkt_depth_recv_q = mkt_depth_recv_q
        self.calibrated_start = False
        self.last_start_time = -1
        self.min_bar_interval = 5

    def reader(self):
        db_client = pymongo.MongoClient()
        print("in reader")
        # calibrate start time to nearest 1 minute
        while True:
            cur_time = int(time.time())
            print("Time: ", cur_time)
            if cur_time % self.min_bar_interval == 0:
                self.calibrated_start = True
                self.last_start_time = cur_time
                break
            if not self.mkt_depth_recv_q.empty():
                data_dict = self.mkt_depth_recv_q.get(block=False)
                self.handle_data(data_dict)

        print("exit calibration")
        self.reset_data()
        while self.calibrated_start:

            if not self.mkt_depth_recv_q.empty():
                data_dict = self.mkt_depth_recv_q.get(block=False)
                self.handle_data(data_dict)
            cur_time = int(time.time())
            # if the time interval is full, then send the statics and reset them
            if cur_time - self.last_start_time >= self.min_bar_interval:
                self.send_data()
                self.last_start_time = cur_time
                self.reset_data()

    def handle_data(self, rt_data):
        # if changing current trading price of an exchange:
        if rt_data["tick_type"] == 4:
            req_id = rt_data["req_id"]
            symbol = self.mkt_data_req_dict[req_id]["symbol"]
            price = rt_data["price"]
            self.mkt_data_req_dict[req_id]["last_price"] = price

            if self.mkt_data_stat_dict[symbol]["high"] == -1 or self.mkt_data_stat_dict[symbol]["high"] < price:
                self.mkt_data_stat_dict[symbol]["high"] = price

            if self.mkt_data_stat_dict[symbol]["low"] == -1 or self.mkt_data_stat_dict[symbol]["low"] > price:
                self.mkt_data_stat_dict[symbol]["low"] = price


            if self.mkt_data_stat_dict[symbol]["open"] == -1:
                self.mkt_data_stat_dict[symbol]["open"] = price
            self.mkt_data_stat_dict[symbol]["cur_price"] = price

        # if new trade is make for an exchange:
        elif rt_data["tick_type"] == 5:
            req_id = rt_data["req_id"]
            symbol = self.mkt_data_req_dict[req_id]["symbol"]
            volume = rt_data["volume"]
            new_volume = self.mkt_data_stat_dict[symbol]["volume"] + volume
            if volume > 0:
                _price = self.mkt_data_req_dict[req_id]["last_price"] if self.mkt_data_req_dict[req_id]["last_price"] != -1 else self.mkt_data_stat_dict[self.mkt_data_req_dict[req_id]["symbol"]]["cur_price"]
                self.mkt_data_stat_dict[symbol]["WAP"] =round( (self.mkt_data_stat_dict[symbol]["WAP"] * self.mkt_data_stat_dict[symbol]["volume"] + _price * volume)/new_volume, 6)
            self.mkt_data_stat_dict[symbol]["volume"] = new_volume
            self.mkt_data_stat_dict[symbol]["count"] += 1

    def send_data(self):
        for symbol, stat_dict in self.mkt_data_stat_dict.items():
            post = {
                    "high": stat_dict["high"] if stat_dict["high"] != -1 else stat_dict["cur_price"],
                    "volume": stat_dict["volume"],
                    "WAP": round(stat_dict["WAP"], 2) if stat_dict["WAP"] != 0 else stat_dict["cur_price"],
                    "low": stat_dict["low"] if stat_dict["low"] != -1 else stat_dict["cur_price"],
                    "open": stat_dict["open"] if stat_dict["open"] != -1 else stat_dict["cur_price"],
                    "close": stat_dict["cur_price"],
                    "time": stat_dict["time"],
                    "datetime": stat_dict["datetime"],
                    "count": stat_dict["count"]
            }
            stat_dict["output_q"].put(post)

    def reset_data(self):
        for symbol, stat_dict in self.mkt_data_stat_dict.items():
            stat_dict["high"] = -1
            stat_dict["volume"] = 0
            stat_dict["WAP"] = 0
            stat_dict["low"] = -1
            stat_dict["open"] = -1
            stat_dict["close"] = -1
            stat_dict["time"] = self.last_start_time
            stat_dict["datetime"] = datetime.datetime.today()
            stat_dict["count"] = 0
