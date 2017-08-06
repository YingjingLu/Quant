import multiprocessing as mp
import time
from constants import UTIL_CST, STK_CST
from trading_contracts import ContractCreateMethods as ct
from trading_orders import OrderCreateMethods as od
from general_util import *
import pymongo

# messge format {price:3, volumn: 8}

class StockAnalysis(mp.Process):

    def __init__(self, symbol, recv_rt_bar_q, recv_rt_price_q, send_order_q, recv_order_q, send_log_q):
        super().__init__(target = self.reader, args = ())
        self.symbol = symbol
        self.next_order_id = 10


        self.recv_rt_bar_q = recv_rt_bar_q
        self.recv_rt_price_q = recv_rt_price_q
        self.send_order_q = send_order_q
        self.recv_order_q = recv_order_q
        self.send_log_q = send_log_q

        self.send_log_q.put([self.pid, 1])

        self.delta_percentage = 0.0025
        self.slop_threshold = 0.2
        self.one_side_count = 3
        self.wm_mid_voltality_threshold = 0.004

        # sorted by time

        self.support_w_list = list()
        # {"high1": {high1_dict}, "high1_index": 17, "low1":{low1_dict},"low1_index":12, "high2":{high_2_dict}, }
        self.pressure_m_list = list()
        # index:{low/high_dict}
        self.today_low_dict = dict()
        self.today_high_dict = dict()

        self.today_first_bar = True
        self.index = 0
        self.low_to_high = 0
        self.high_to_low = 0
        self.finding_high = True
        self.today_first_high_low = True
        # list of orders always sorted by
        self.order_dict = dict()
        self.pre_order_dict = dict()
        self.existing_order_id_set = set()

        self.rt_bar_accum_count = 0
        self.calc_bar_size = "1 min"
        self.rt_bar_accum_max = QUERY_CST.RT_BAR_BAR_SIZE_TO_SEC[self.calc_bar_size] // 5
        print( self.rt_bar_accum_max)
        self.rt_bar_accum_dict = dict()
        self.rt_bar_calibrated = False

        #self.log_file = open("SA_LOG.txt", "wb")
        print("finish SA init")


    def reader(self):
        db_client = pymongo.MongoClient()

        db_name = symbol_to_db_name(self.symbol)
        db = db_client[db_name]
        while True:
            if not self.recv_rt_bar_q.empty():
                rt_bar = self.recv_rt_bar_q.get(block=False)
                if rt_bar == 0:
                    self.send_order_q.put(0)
                    self.send_log_q([self.pid, 0])
                    break
                else:
                    self.rt_bar_handler(rt_bar, db)
            if not self.recv_order_q.empty():
                order_feedback = self.recv_order_q.get(block=False)
                self.put_successful_order_to_list(order_feedback)
        self.join()

    def rt_bar_handler(self, rt_dict, db):
        # print("RealTime_Bar: ", rt_dict)
        db[convert_RT_collection_name("5 secs")].insert_one(rt_dict)
        #self.log_file.write("Got 5sec RT Bar: " + str(rt_dict) + "\n")
        if (self.rt_bar_calibrated == False) and (rt_dict["time"] % QUERY_CST.RT_BAR_BAR_SIZE_TO_SEC[self.calc_bar_size] == 0):
            self.rt_bar_calibrated = True
        if self.rt_bar_calibrated == False:
            return

        if self.rt_bar_accum_count == 0:
            self.rt_bar_accum_dict = rt_dict
            self.rt_bar_accum_count += 1
        else:
            if rt_dict["volume"] != 0:
                if self.rt_bar_accum_dict["high"] < rt_dict["high"]:
                    self.rt_bar_accum_dict["high"] = rt_dict["high"]
                if self.rt_bar_accum_dict["low"] > rt_dict["low"]:
                    self.rt_bar_accum_dict["low"] = rt_dict["low"]
                self.rt_bar_accum_dict["WAP"] = (self.rt_bar_accum_dict["WAP"]*self.rt_bar_accum_dict["volume"] + rt_dict["WAP"]*rt_dict["volume"])/(self.rt_bar_accum_dict["volume"] + rt_dict["volume"])
                self.rt_bar_accum_dict["volume"] = self.rt_bar_accum_dict["volume"] + rt_dict["volume"]
                self.rt_bar_accum_dict["count"] = self.rt_bar_accum_dict["count"] + rt_dict["count"]
            self.rt_bar_accum_count += 1
            if self.rt_bar_accum_count == self.rt_bar_accum_max:
                self.rt_bar_accum_dict["close"] = rt_dict["close"]
                self.rt_bar_accum_dict["WAP"] = round(self.rt_bar_accum_dict["WAP"], 2)
                #print("RT Bar: ", self.rt_bar_accum_dict)
                #self.log_file.write("RT Bar: " + str(self.rt_bar_accum_dict) + "\n")
                self.calc_WAP_low_high(self.rt_bar_accum_dict, db)
                self.rt_bar_accum_count = 0
        self.determine_order(rt_dict)
    """
    def calc_WAP_low_high(self, rt_dict, db):
        db[convert_RT_collection_name(self.calc_bar_size)].insert_one(rt_dict)
        self.cur_WAP = rt_dict["WAP"]
        if self.today_first_high_low:
            if self.today_first_bar:
                self.cur_low = rt_dict["WAP"]
                self.cur_high = rt_dict["WAP"]
                self.cur_WAP = rt_dict["WAP"]
                self.cur_low_dict = rt_dict
                self.cur_high_dict = rt_dict
                self.today_first_bar = False
            else:
                if self.cur_WAP <= self.cur_low:
                    self.cur_low = self.cur_WAP
                    self.cur_low_dict = rt_dict
                    # end checking ignored middle high
                    self.low_to_high = 0
                    self.high_to_low += 1
                    # print("New Low: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                    print("New Low: ", rt_dict)
                    #self.log_file.write("New Low: " + str(rt_dict) + "\n")
                elif self.cur_WAP >= self.cur_high:
                    self.low_to_high += 1
                    self.high_to_low = 0
                    self.cur_high = self.cur_WAP
                    # print("New High: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                    print("New High: ", rt_dict)
                    #self.log_file.write("Change Cur High: " + str(rt_dict) + "\n")
                    self.cur_high_dict = rt_dict
                else:
                    self.high_to_low += 1
                    self.low_to_high += 1
                if self.high_to_low >= self.one_side_count:
                    self.today_high_dict[self.index] = self.cur_high_dict
                    self.index += 1
                    self.low_to_high = 0

                    self.finding_high = False

                    self.today_first_high_low = False
                    print("...................")
                    # print("After inserting new High:  ", self.cur_high_dict["WAP"], " @ ", self.cur_high_dict["datetime"])
                    print("After inserting new High:  ", self.cur_high_dict)
                    print("...................")

                elif self.low_to_high >= self.one_side_count:
                    self.today_low_dict[self.index] = self.cur_low_dict
                    self.index += 1
                    self.high_to_low = 0

                    self.finding_high = True
                    self.today_first_high_low = False
                    print("...................")
                    # print("After inserting new Low:  ", self.cur_low_dict["WAP"], " @ ", self.cur_low_dict["datetime"])
                    print("After inserting new Low:  ", self.cur_low_dict)
                    print("...................")

        else:


            # turing from increasing to decreasing

            # update if new low appears
            if self.cur_WAP <= self.cur_low:
                self.cur_low = self.cur_WAP
                self.cur_low_dict = rt_dict
                # end checking ignored middle high
                self.low_to_high = 0
                self.high_to_low += 1
                # print("New Low: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                print("New Low: ", rt_dict)
                #self.log_file.write("New Low: " + str(rt_dict) + "\n")
            elif self.cur_WAP >= self.cur_high:
                self.low_to_high += 1
                self.high_to_low = 0
                self.cur_high = self.cur_WAP
                # print("New High: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                print("New High: ", rt_dict)
                #self.log_file.write("Change Cur High: " + str(rt_dict) + "\n")
                self.cur_high_dict = rt_dict
            else:
                if self.finding_high == True:
                    self.high_to_low += 1

                    if self.high_to_low > self.one_side_count:
                        start_time = self.cur_low_dict["time"]
                        end_time = rt_dict["time"]
                        recent_max_dict = self.find_RT_interval_WAP_min_max("MAX", self.calc_bar_size, start_time, end_time, db)[-1]
                        print("more than 3 bars after high")
                        if abs(recent_max_dict["time"] - start_time)//(5*self.rt_bar_accum_max) >= self.one_side_count:
                            # switch to find low
                            self.finding_high = False
                            # print("switch to find low @: ", rt_dict)

                            #self.log_file.write("switch to find low @: " + str(rt_dict) + "\n")
                            # record last low
                            #self.today_low_dict[self.index] = self.cur_low_dict
                            self.today_high_dict[self.index] = recent_max_dict
                            print("...................")
                            # print("After inserting new High:  ", recent_max_dict["WAP"], " @ ", recent_max_dict["datetime"])
                            print("After inserting new High:  ", recent_max_dict)
                            print("...................")
                            self.add_top_m()
                            self.index += 1
                            # switch to new low ## MODIFIED ##
                            # self.cur_low = self.cur_WAP
                            # self.cur_low_dict = rt_dict
                            self.cur_high = recent_max_dict["WAP"]
                            self.cur_high_dict = recent_max_dict
                            self.low_to_high = 0

                else:
                    self.low_to_high += 1
                    if self.low_to_high > self.one_side_count:
                        print("more than 3 bars after low")
                        start_time = self.cur_high_dict["time"]
                        end_time = rt_dict["time"]
                        recent_min_dict = self.find_RT_interval_WAP_min_max("MIN", self.calc_bar_size, start_time, end_time, db)[-1]

                        if abs(recent_min_dict["time"] - start_time)//(5*self.rt_bar_accum_max) >= self.one_side_count:
                            # switch to find high
                            self.finding_high = True

                            # print("switch to find high @: ", rt_dict)

                            #self.log_file.write("switch to find high @: " + str(rt_dict) + "\n")
                            # record last high
                            #self.today_high_dict[self.index] = self.cur_high_dict
                            self.today_low_dict[self.index] = recent_min_dict
                            print("...................")
                            # print("After inserting new Low:  ", recent_min_dict["WAP"], " @ ", recent_min_dict["datetime"])
                            print("After inserting new Low:  ", recent_min_dict)
                            print("...................")
                            self.add_bottom_w()
                            self.index += 1
                            # switch to new high ### MIDOFIED ##
                            self.cur_low = recent_min_dict["WAP"]
                            self.cur_low_dict = recent_min_dict
                            self.high_to_low = 0
    """
    def calc_WAP_low_high(self, rt_dict, db):
        db[convert_RT_collection_name(self.calc_bar_size)].insert_one(rt_dict)
        self.cur_WAP = rt_dict["WAP"]
        if self.today_first_high_low:
            if self.today_first_bar:
                self.cur_low = rt_dict["WAP"]
                self.cur_high = rt_dict["WAP"]
                self.cur_WAP = rt_dict["WAP"]
                self.cur_low_dict = rt_dict
                self.cur_high_dict = rt_dict
                self.today_first_bar = False
            else:
                if self.cur_WAP <= self.cur_low:
                    self.cur_low = self.cur_WAP
                    self.cur_low_dict = rt_dict
                    # end checking ignored middle high
                    self.low_to_high = 0
                    self.high_to_low += 1
                    # print("New Low: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                    print("New Low: ", rt_dict)
                    #self.log_file.write("New Low: " + str(rt_dict) + "\n")
                elif self.cur_WAP >= self.cur_high:
                    self.low_to_high += 1
                    self.high_to_low = 0
                    self.cur_high = self.cur_WAP
                    # print("New High: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                    print("New High: ", rt_dict)
                    #self.log_file.write("Change Cur High: " + str(rt_dict) + "\n")
                    self.cur_high_dict = rt_dict
                else:
                    self.high_to_low += 1
                    self.low_to_high += 1
                if self.high_to_low >= self.one_side_count:
                    self.today_high_dict[self.index] = self.cur_high_dict
                    self.index += 1
                    self.low_to_high = 0

                    self.finding_high = False

                    self.today_first_high_low = False
                    print("...................")
                    # print("After inserting new High:  ", self.cur_high_dict["WAP"], " @ ", self.cur_high_dict["datetime"])
                    print("After inserting new High:  ", self.cur_high_dict)
                    print("...................")

                elif self.low_to_high >= self.one_side_count:
                    self.today_low_dict[self.index] = self.cur_low_dict
                    self.index += 1
                    self.high_to_low = 0

                    self.finding_high = True
                    self.today_first_high_low = False
                    print("...................")
                    # print("After inserting new Low:  ", self.cur_low_dict["WAP"], " @ ", self.cur_low_dict["datetime"])
                    print("After inserting new Low:  ", self.cur_low_dict)
                    print("...................")

        else:


            # turing from increasing to decreasing

            # update if new low appears
            if self.cur_WAP <= self.cur_low:
                self.cur_low = self.cur_WAP
                self.cur_low_dict = rt_dict
                # end checking ignored middle high
                self.low_to_high = 0
                self.high_to_low += 1
                # print("New Low: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                print("New Low: ", rt_dict)
                #self.log_file.write("New Low: " + str(rt_dict) + "\n")

                if self.finding_high:
                    if self.high_to_low > self.one_side_count:
                        start_time = self.cur_low_dict["time"]
                        end_time = rt_dict["time"]
                        recent_max_dict = self.find_RT_interval_WAP_min_max("MAX", self.calc_bar_size, start_time, end_time, db)[-1]
                        print("more than 3 bars after high")
                        if abs(recent_max_dict["time"] - start_time)//(5*self.rt_bar_accum_max) >= self.one_side_count:
                            # switch to find low
                            self.finding_high = False
                            # print("switch to find low @: ", rt_dict)

                            #self.log_file.write("switch to find low @: " + str(rt_dict) + "\n")
                            # record last low
                            #self.today_low_dict[self.index] = self.cur_low_dict
                            self.today_high_dict[self.index] = recent_max_dict
                            print("...................")
                            # print("After inserting new High:  ", recent_max_dict["WAP"], " @ ", recent_max_dict["datetime"])
                            print("After inserting new High:  ", recent_max_dict)
                            print("...................")
                            self.add_top_m()
                            self.index += 1
                            # switch to new low ## MODIFIED ##
                            # self.cur_low = self.cur_WAP
                            # self.cur_low_dict = rt_dict
                            self.cur_high = recent_max_dict["WAP"]
                            self.cur_high_dict = recent_max_dict
                            self.low_to_high = 0
                        else:
                            if self.today_low_dict.get(self.index -1) != None:
                                self.today_low_dict[self.index -1] = rt_dict
                                print("Update Last Low to: ", rt_dict)
                    else:
                        if self.today_low_dict.get(self.index -1) != None:
                            self.today_low_dict[self.index -1] = rt_dict
                            print("Update Last Low to: ", rt_dict)
            elif self.cur_WAP >= self.cur_high:
                self.low_to_high += 1
                self.high_to_low = 0
                self.cur_high = self.cur_WAP
                # print("New High: ", rt_dict["WAP"], " @ ", rt_dict["datetime"])
                print("New High: ", rt_dict)
                #self.log_file.write("Change Cur High: " + str(rt_dict) + "\n")
                self.cur_high_dict = rt_dict

                if self.finding_high == False:
                    if self.low_to_high > self.one_side_count:
                        print("more than 3 bars after low")
                        start_time = self.cur_high_dict["time"]
                        end_time = rt_dict["time"]
                        recent_min_dict = self.find_RT_interval_WAP_min_max("MIN", self.calc_bar_size, start_time, end_time, db)[-1]

                        if abs(recent_min_dict["time"] - start_time)//(5*self.rt_bar_accum_max) >= self.one_side_count:
                            # switch to find high
                            self.finding_high = True

                            # print("switch to find high @: ", rt_dict)

                            #self.log_file.write("switch to find high @: " + str(rt_dict) + "\n")
                            # record last high
                            #self.today_high_dict[self.index] = self.cur_high_dict
                            self.today_low_dict[self.index] = recent_min_dict
                            print("...................")
                            # print("After inserting new Low:  ", recent_min_dict["WAP"], " @ ", recent_min_dict["datetime"])
                            print("After inserting new Low:  ", recent_min_dict)
                            print("...................")
                            self.add_bottom_w()
                            self.index += 1
                            # switch to new high ### MIDOFIED ##
                            self.cur_low = recent_min_dict["WAP"]
                            self.cur_low_dict = recent_min_dict
                            self.high_to_low = 0
                        else:
                            if self.today_high_dict.get(self.index -1) != None:
                                self.today_high_dict[self.index -1] = rt_dict
                                print("Update Last high to: ", rt_dict)
                    else:
                        if self.today_high_dict.get(self.index -1) != None:
                            self.today_high_dict[self.index -1] = rt_dict
                            print("Update Last high to: ", rt_dict)

            else:
                if self.finding_high == True:
                    self.high_to_low += 1

                    if self.high_to_low > self.one_side_count:
                        start_time = self.cur_low_dict["time"]
                        end_time = rt_dict["time"]
                        recent_max_dict = self.find_RT_interval_WAP_min_max("MAX", self.calc_bar_size, start_time, end_time, db)[-1]
                        print("more than 3 bars after high")
                        if abs(recent_max_dict["time"] - start_time)//(5*self.rt_bar_accum_max) >= self.one_side_count:
                            # switch to find low
                            self.finding_high = False
                            # print("switch to find low @: ", rt_dict)

                            #self.log_file.write("switch to find low @: " + str(rt_dict) + "\n")
                            # record last low
                            #self.today_low_dict[self.index] = self.cur_low_dict
                            self.today_high_dict[self.index] = recent_max_dict
                            print("...................")
                            # print("After inserting new High:  ", recent_max_dict["WAP"], " @ ", recent_max_dict["datetime"])
                            print("After inserting new High:  ", recent_max_dict)
                            print("...................")
                            self.add_top_m()
                            self.index += 1
                            # switch to new low ## MODIFIED ##
                            # self.cur_low = self.cur_WAP
                            # self.cur_low_dict = rt_dict
                            self.cur_high = recent_max_dict["WAP"]
                            self.cur_high_dict = recent_max_dict
                            self.low_to_high = 0

                else:
                    self.low_to_high += 1
                    if self.low_to_high > self.one_side_count:
                        print("more than 3 bars after low")
                        start_time = self.cur_high_dict["time"]
                        end_time = rt_dict["time"]
                        recent_min_dict = self.find_RT_interval_WAP_min_max("MIN", self.calc_bar_size, start_time, end_time, db)[-1]

                        if abs(recent_min_dict["time"] - start_time)//(5*self.rt_bar_accum_max) >= self.one_side_count:
                            # switch to find high
                            self.finding_high = True

                            # print("switch to find high @: ", rt_dict)

                            #self.log_file.write("switch to find high @: " + str(rt_dict) + "\n")
                            # record last high
                            #self.today_high_dict[self.index] = self.cur_high_dict
                            self.today_low_dict[self.index] = recent_min_dict
                            print("...................")
                            # print("After inserting new Low:  ", recent_min_dict["WAP"], " @ ", recent_min_dict["datetime"])
                            print("After inserting new Low:  ", recent_min_dict)
                            print("...................")
                            self.add_bottom_w()
                            self.index += 1
                            # switch to new high ### MIDOFIED ##
                            self.cur_low = recent_min_dict["WAP"]
                            self.cur_low_dict = recent_min_dict
                            self.high_to_low = 0
    # Assume that the function is called when a new low is added AND index has NOT been incremented
    def add_bottom_w(self):
        cur_low_index = self.index
        cur_low_dict = self.today_low_dict[self.index]
        cur_low_WAP = cur_low_dict["WAP"]
        prev_estab_low1 = []
        for low_index in range(cur_low_index % 2, cur_low_index, 2):
            low_dict = self.today_low_dict[low_index]
            low_WAP = low_dict["WAP"]
            if low_WAP <= cur_low_WAP:
                # check if the node is lower than all prev established low1s
                is_lower_than_all_prev_low1 = True
                for low_val in prev_estab_low1:
                    if low_WAP >= low_val:
                        is_lower_than_all_prev_low1 = False
                # if there is at least one low1 that is in the middle and lower, then skip
                if is_lower_than_all_prev_low1 == False:
                    continue
                # get the highest mid-high
                high_dict = dict()
                high_WAP = 0
                high_index = 0
                for high_i in range(cur_low_index - 1, low_index, -2):
                    if self.today_high_dict[high_i]["WAP"] >= high_WAP:
                        high_WAP = self.today_high_dict[high_i]["WAP"]
                        high_dict = self.today_high_dict[high_i]
                        high_index = high_i
                # construct the dictionary of new bottom w dictionary
                if high_dict != dict():
                    # add minium volatility threshold
                    if min( (high_WAP-cur_low_WAP)/cur_low_WAP,
                            (high_WAP-low_WAP)/low_WAP ) >= self.wm_mid_voltality_threshold:

                        start_high = dict()
                        start_high_index = 0
                        for sh_index in range(high_index-2, -1, -2):
                            if ((sh_index < low_index) and (self.today_high_dict[sh_index]["WAP"] >= self.today_high_dict[high_index]["WAP"])):
                                start_high = self.today_high_dict[sh_index]
                                start_high_index = sh_index
                                break
                        new_w_dict = {
                                      "low1_dict": self.today_low_dict[low_index],
                                      "low1_index": low_index,
                                      "low2_dict": cur_low_dict,
                                      "low2_index": cur_low_index,
                                      "mid_high_dict": self.today_high_dict[high_index],
                                      "mid_high_index": high_index,
                                      "start_high": start_high,
                                      "start_high_index": start_high_index
                        }
                        self.support_w_list.append(new_w_dict)
                        print("New_bottom_w: ", new_w_dict)
                        #self.log_file.write("New_bottom_w: " + str(new_w_dict) + "\n")



    # assume that the function is called when a new high is added
    def add_top_m(self):
        cur_high_index = self.index
        cur_high_dict = self.today_high_dict[self.index]
        cur_high_WAP = cur_high_dict["WAP"]
        prev_estab_high1 = []
        for high_index in range(cur_high_index % 2, cur_high_index, 2):
            high_dict = self.today_high_dict[high_index]
            high_WAP = high_dict["WAP"]
            if high_WAP <= cur_high_WAP:
                # check if the node is higher than all prev established highs
                is_higher_than_all_prev_high1 = True
                for high_val in prev_estab_high1:
                    if high_WAP <= high_val:
                        is_higher_than_all_prev_high1 = False
                # if there is at least one low1 that is in the middle and lower, then skip
                if is_higher_than_all_prev_high1 == False:
                    continue
                # get the highest mid_low:
                low_dict = dict()
                low_WAP = 0
                low_index = 0
                for low_i in range(cur_high_index-1, high_index, -2):
                    if self.today_low_dict[low_i]["WAP"] >= low_WAP:
                        low_WAP = self.today_low_dict[low_i]["WAP"]
                        low_dict = self.today_low_dict[low_i]
                        low_index = low_i
                if low_dict != dict():
                    # check for wm volatility threshold
                    if min( (cur_high_WAP - low_WAP)/cur_high_WAP,
                            (high_WAP-low_WAP)/high_WAP ) >= self.wm_mid_voltality_threshold:
                        start_low = dict()
                        start_low_index = 0
                        for sl_index in range(low_index - 2, -1, -2):
                            if ((sl_index < high_index) and (self.today_low_dict[sl_index]["WAP"] <= self.today_low_dict[low_index]["WAP"] )):
                                start_low = self.today_low_dict[sl_index]
                                start_low_index = sl_index
                                break
                        new_w_dict = {
                                      "high1_dict": high_dict,
                                      "high1_dict_index": high_index,
                                      "high2_dict": cur_high_dict,
                                      "high2_dict_index": cur_high_index,
                                      "mid_low_dict": low_dict,
                                      "mid_low_index": low_index,
                                      "start_low": start_low,
                                      "start_low_index": start_low_index
                        }
                        self.pressure_m_list.append(new_w_dict)
                        print("New_top_w", new_w_dict)
                        #self.log_file.write("New_top_w: " + str(new_w_dict) + "\n")

    def remove_pressure_m(self, rt_bar):
        rt_WAP = rt_bar["WAP"]
        for m_dict_index in range(len(self.pressure_m_list) - 1, -1, -1):
            if self.pressure_m_list[m_dict_index] != dict():
                if rt_WAP <= self.pressure_m_list[m_dict_index]["start_low"]:
                    print("Cur RT_BAR: ", rt_bar)
                    print("Remove Pressure M: ", self.pressure_m_list[m_dict_index])
                    self.pressure_m_list[m_dict_index] = dict()



    def remove_support_w(self, rt_bar):
        rt_WAP = rt_bar["WAP"]
        for w_dict_index in range(len(self.support_w_list)-1, -1, -1):
            if self.support_w_list[w_dict_index] != dict():
                if rt_WAP >= self.support_w_list[w_dict_index]["start_high"]:
                    print("Cur RT_BAR: ". rt_bar)
                    print("Remove Support W: ", self.support_w_list[w_dict_index])
                    self.support_w_list[w_dict_index] = dict()

    def determine_order(self,rt_bar):
        self.determine_sell(rt_bar)
        rt_WAP = rt_bar["WAP"]
        # go over each order in the order list, update their highest gain if new high
        # determine if a existing order needs to be sold
        # determine if BUY
        # go over each supportive w see if WAP is higher than mid high
        dropped_w_list = []
        for w_dict_index in range(len(self.support_w_list)-1, -1, -1):
            if self.support_w_list[w_dict_index]["mid_high_dict"]["WAP"] <= rt_WAP:
                dropped_w_list.append(self.support_w_list[w_dict_index])
                # print("Remove W: ", self.support_w_list[w_dict_index] )
                #self.log_file.write("Remove W: " + str(self.support_w_list[w_dict_index]) + "\n")
                self.support_w_list.remove(self.support_w_list[w_dict_index])
        # go over each m to see if the WAP is lower than mid low
        if dropped_w_list != []:
            self.send_BUY_order(dropped_w_list, rt_bar)
        for m_dict_index in range(len(self.pressure_m_list)-1, -1, -1):
            if self.pressure_m_list[m_dict_index]["mid_low_dict"]["WAP"] >= rt_WAP:
                ####
                #### THIS PLACE NEED MORE CONSTRUCTION
                ####
                # print("Remove M: ", self.pressure_m_list[m_dict_index] )
                #self.log_file.write("Remove M: " + str(self.pressure_m_list[m_dict_index]) + "\n")
                self.pressure_m_list.remove(self.pressure_m_list[m_dict_index])
    """
    # ORDER: {
              "order_id":
              "order_start_pos":
              "order_amount":
              "order_low":
              "order_mid_high":
              "highest_gain":
              "highest_gain_percentage":
              "stop_pos"
              }
    """


    def determine_sell(self, rt_bar):
        min_price = rt_bar["low"]
        for order_dict in self.order_dict.values():
            start_price = order_dict["start_position"]
            if min_price <= order_dict["order_low"]:
                self.place_sell_order(order_dict)
                #self.log_file.write("Stop Loss : Order: " + str(order_dict) + "rt_bar: "+(rt_bar)+"\n")
            else:
                highest_gain = order_dict["highest_gain"]
                highest_gain_percentage = order_dict["highest_gain_percentage"]
                cur_gain = rt_bar["close"] - start_price
                gain_percentage = cur_gain / start_price

                if cur_gain > highest_gain:
                     order_dict["highest_gain"] = cur_gain
                     order_dict["highest_gain_percentage"] = gain_percentage

                elif 0.005<= highest_gain_percentage < 0.015:
                    if cur_gain / highest_gain <= 0.55:
                        self.place_sell_order(order_dict)
                elif 0.015<= highest_gain_percentage < 0.03:
                    if cur_gain / highest_gain <= 0.4:
                        self.place_sell_order(order_dict)
                elif 0.03<= highest_gain_percentage < 0.05:
                    if cur_gain / highest_gain <= 0.75:
                        self.place_sell_order(order_dict)
                elif 0.05<= highest_gain_percentage:
                    if cur_gain / highest_gain <= 0.7:
                        self.place_sell_order(order_dict)

    def send_BUY_order(self, w_dict_list, rt_bar):
        order_id = self.nextOrderId()
        limit_price = rt_bar["WAP"] + 0.01
        send_order = {
                 "order_id": order_id,
                 "product_type": "STK",
                 "symbol": self.symbol,
                 "limit_price": limit_price,
                 "action": "BUY",
                 "sell_price": None,
                 "is_mkt_order": False,
                 "start_position":0.0,
                 "amount":0
        }
        self.send_order_q.put(send_order)

        pre_order = {
                     "order_id": order_id,
                     "product_type": "STK",
                     "symbol": self.symbol,
                     "limit_price": limit_price,
                     "action": "BUY",
                     "sell_price": None,
                     "is_mkt_order": False,
                     "start_position":0.0,
                     "amount":0,
                     "order_low": w_dict_list[0]["low2_dict"]["WAP"],
                     "order_mid_high": w_dict_list[0]["mid_high_dict"]["WAP"],
                     "highest_gain":0,
                     "highest_gain_percentage":0.0
        }
        print("Pre order: ", pre_order)
        self.pre_order_dict[order_id] = pre_order
        #self.log_file.write("Send pre order: " + str(pre_order) +"\n")

    def place_sell_order(self, order_dict):
        order_dict["action"] = "SELL"
        order_dict["is_mkt_order"] = True
        order_dict["sell_order_id"] = self.nextOrderId()
        self.send_order_q.put(order_dict)
        print("Place Sell Order: ", order_dict["start_position"])
        #self.log_file.write("Place sell order: " + str(order_dict) +"\n")

    def put_successful_order_to_list(self, return_order_dict):
        print("Pre Order Dict: ", self.pre_order_dict)
        print("Order Id: ", return_order_dict["order_id"])
        if return_order_dict["order_status"] == "Filled":
            if self.pre_order_dict[return_order_dict["order_id"]]["action"] == "BUY":
                insert_order = self.pre_order_dict[return_order_dict["order_id"]]
                if return_order_dict["avg_fill_price"] != None:
                     insert_order["start_position"] = return_order_dict["avg_fill_price"]
                insert_order["amount"] = return_order_dict["amount"]
                print("---------------------------------")
                print("Order BUY Successfully fill: ", insert_order)
                print("---------------------------------")
            #self.log_file.write("Order successfully fill: " + str(insert_order) +"\n")
                self.order_dict[return_order_dict["order_id"]] = insert_order

        if self.pre_order_dict[return_order_dict["order_id"]]["action"] == "SELL":
            print("-------------------------------------------")
            print("Order SELL Successfully fill: ", self.order_dict[return_order_dict["order_id"]])
            print("-------------------------------------------")
            self.order_dict.pop(return_order_dict["order_id"])

    def find_RT_interval_WAP_min_max(self, min_or_max, bar_size, start_time, end_time, db):
        pipeline = [
                    {"$match" : {"time": {"$gte": start_time, "$lte": end_time}}},
                    {"$group": {
                                "_id": None,
                                "min_WAP": {"$min": "$WAP"},
                                "max_WAP": {"$max": "$WAP"},
                                }
                    }
        ]
        collection = db[convert_RT_collection_name(bar_size)]
        aggregate_result = list(collection.aggregate(pipeline))[0]
        if min_or_max == "MIN":
            cursor = collection.find({"WAP": aggregate_result["min_WAP"]}).sort("time", pymongo.ASCENDING)
        elif min_or_max == "MAX":
            cursor = collection.find({"WAP": aggregate_result["max_WAP"]}).sort("time", pymongo.ASCENDING)
        return list(cursor)

    def nextOrderId(self):
        self.next_order_id += 1
        return self.next_order_id
