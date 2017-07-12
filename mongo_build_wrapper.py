import pymongo
import pprint
import datetime
from bson.objectid import ObjectId
from mongo_query_wrappers import *
from general_util import *
from log_build_error_msg import *
from mongo_log_builder import *
import multiprocessing as mp

def mongo_insert_historical(collection, req_dict,  date: str, _open: float, high: float,
                   low: float, close: float, volume: int, barCount: int,
                   WAP: float, hasGaps: int):

    converted = parse_datetime(date)
    if datetime_exist(collection, converted) == False:
        post = {
                "datetime" : converted,
                "open" : _open,
                "high" : high,
                "low" : low,
                "close" : close,
                "volume" : volume,
                "count" : barCount,
                "WAP" : WAP,
                "hasGaps" : hasGaps
        }
        # print(">>> Post: ", end = "")
        # pprint.pprint(post)
        collection.insert_one(post)
        if req_dict["start_toggle"] == True:
            req_dict["last_start"] = converted
            req_dict["start_toggle"] = False
        return True
    else:
        if req_dict["start_toggle"] == True:
            req_dict["last_start"] = converted
            req_dict["start_toggle"] = False
        #print("Record Exists")
        return False

def mongo_insert_stk_historical_wrapper(db_client,req_id, query_dict,  date: str,
                                        _open: float, high: float,
                                       low: float, close: float, volume: int,
                                       barCount: int,
                                       WAP: float, hasGaps: int):
    symbol = query_dict[req_id]["symbol"]
    what_to_do = query_dict[req_id]["what_to_do"]
    bar_size = query_dict[req_id]["bar_size"]

    db_name = "STK_" + symbol
    collection_name = what_to_do + bar_size
    collection = db_client[db_name][collection_name]
    mongo_insert_historical(collection, date, _open, high, low,
                            close, volume, barCount, WAP, hasGaps)




#   Convert 5sec bar size collection into other sized collection #

# include start not include end
def conclude_interval_TRADES(prev_collection, collection, start_dt, end_dt, db_client, symbol, bar_size):
    print("Start Conclude From: ", start_dt, " To ", end_dt)
    query = prev_collection.find({"datetime": {"$gte": start_dt, "$lt": end_dt}}).sort("datetime", pymongo.DESCENDING)
    count = query.count()
    if  count == 0:
        print("Error: No Record ", prev_collection, " From: ", start_dt, " To: ", end_dt, "Has no result")
        STK_historical_log_build(db_client, symbol, "TRADES",
                                 bar_size, start_dt, end_dt, False, 3)
        return
    pipeline = [
                {"$match" : {"datetime": {"$gte": start_dt, "$lt": end_dt}}},
                {"$group": {
                            "_id": None,
                            "low_open": {"$min": "$open"},
                            "low_close": {"$min": "$close"},
                            "low_low": {"$min": "$low"},

                            "high_open": {"$max": "$open"},
                            "high_close": {"$max": "$close"},
                            "high_high": {"$max": "$high"},

                            "sum_vol": {"$sum": "$volume"},
                            "sum_bar_count": {"$sum": "$count"}
                            }
                }
    ]
    aggregate_result = list(prev_collection.aggregate(pipeline))[0]
    total_volume = aggregate_result["sum_vol"]
    total_bar_count = aggregate_result["sum_bar_count"]
    total_low = min(aggregate_result["low_open"],
                    aggregate_result["low_close"],
                    aggregate_result["low_low"]
                    )
    total_high = max(aggregate_result["high_open"],
                     aggregate_result["high_close"],
                     aggregate_result["high_high"]
                     )
    query_list = list(query)
    close = query_list[0]["close"]
    _open = query_list[-1]["open"]
    total_WAP = 0
    total_hasGaps = False
    for elem in query_list:
        total_WAP += elem["WAP"] * elem["volume"]
        total_hasGaps = total_hasGaps or elem["hasGaps"]
    if total_volume == 0:
        total_WAP = round((query_list[-1]["WAP"] + query_list[0]["WAP"]) / 2, 2)
    else:
        total_WAP = round(total_WAP / total_volume, 2)

    result_dict = {
                    "datetime" : start_dt,
                    "open" : _open,
                    "high" : total_high,
                    "low" : total_low,
                    "close" : close,
                    "volume" : total_volume,
                    "count" : total_bar_count,
                    "WAP" : total_WAP,
                    "hasGaps" : total_hasGaps
    }
    collection.insert_one(result_dict)
    if total_hasGaps:
        STK_historical_log_build(db_client, symbol, "TRADES",
                                 bar_size, start_dt, end_dt, False, 1)
    else:
        STK_historical_log_build(db_client, symbol, "TRADES",
                                 bar_size, start_dt, end_dt, True)


def conclude_interval_TRADES_wrapper(db_client, symbol):
    db = db_client[symbol_to_db_name(symbol)]
    bar_size_list = QUERY_CST.DB_AVAILABLE_BAR_SIZE_LIST
    for bar_size_index in range(1, len(bar_size_list)):

        prev_bar_size = bar_size_list[bar_size_index - 1]
        bar_size = bar_size_list[bar_size_index]

        prev_collection =db[convert_collection_name("TRADES", prev_bar_size)]
        collection = db[convert_collection_name("TRADES", bar_size)]
        print("In Collection: " + convert_collection_name("TRADES", bar_size) + "\n")
        print("Prev Collection: " + convert_collection_name("TRADES", prev_bar_size) + "\n")

        # update_start_dt------cur_start_dt////////////cur_end_dt-------update_end_dt

        update_start_dt = find_whole_start_dt(prev_collection, bar_size)
        update_end_dt = find_whole_end_dt(prev_collection, prev_bar_size, bar_size)

        print("Prev Collection Start: " + str(find_whole_start_dt(prev_collection, bar_size)) + "\n")
        print("Prev Collection End: " + str(find_whole_end_dt(prev_collection, prev_bar_size, bar_size)) + "\n")

        delta = QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[bar_size]

        if prev_collection.find_one() == None:
            print("Error, not building up for previous collection in >> conclude_interval_TRADES_wrapper")
            return

        if collection.find_one() == None:
            first_time = 1
            while(update_start_dt < update_end_dt):
                conclude_interval_TRADES(prev_collection, collection, update_start_dt, update_start_dt + delta, db_client, symbol, bar_size)
                if first_time == 1:
                    collection.create_index([("datetime", pymongo.DESCENDING)])
                    first_time = 0
                update_start_dt += delta
                if not is_in_STK_Trading_hour(update_start_dt):
                    update_start_dt = STK_next_trade_day(update_start_dt)
            STK_historical_operation_log("insert", symbol, db_client, bar_size, update_start_dt, update_end_dt, True)
        else:
            cur_start_dt = earlest_datetime(collection)
            cur_end_dt = most_current_datetime(collection) + delta

            while (update_start_dt < cur_start_dt):
                conclude_interval_TRADES(prev_collection, collection, update_start_dt, delta + update_start_dt, db_client, symbol, bar_size)
                update_start_dt += delta

                if not is_in_STK_Trading_hour(update_start_dt):
                    update_start_dt = STK_next_trade_day(update_start_dt)
            STK_historical_operation_log("insert", symbol, db_client, bar_size, update_start_dt, cur_start_dt, True)

            while(cur_end_dt < update_end_dt):
                conclude_interval_TRADES(prev_collection, collection, cur_end_dt, cur_end_dt + delta, db_client, symbol, bar_size)
                cur_end_dt += delta
                if not is_in_STK_Trading_hour(cur_end_dt):
                    cur_end_dt = STK_next_trade_day(cur_end_dt)
            STK_historical_operation_log("insert", symbol, db_client, bar_size, cur_end_dt, update_end_dt, True)
    print(symbol, " Finishes")

def f(q, x):
    while x <= 10000:
        x += 1
        if x %50 == 0:
            q.put(x)
def writer(q):
    db_client = pymongo.MongoClient()
    for i in range(0, q):
        db_client["test_1"]["test1"].insert_one({"test": i})
    db_client.close()
def writer2(q):
    db_client = pymongo.MongoClient()
    for i in range(0, q):
        db_client["test_2"]["test_2"].insert_one({"test": i})
    db_client.close()
"""
def run_main():
    # lst = ["NVDA", "BABA"]
    # BABA_p = mp.Process(target = conclude_interval_TRADES_wrapper, args = (pymongo.MongoClient(),"BABA"))
    # NVDA_p = mp.Process(target = conclude_interval_TRADES_wrapper, args = (pymongo.MongoClient(),"NVDA"))
    # BABA_p = mp.Process(target = f, args = ("BABA",))
    # NVDA_p = mp.Process(target = f, args = ("NVDA",))
    # BABA_p.start()
    # NVDA_p.start()
    # BABA_p.join()
    # NVDA_p.join()
    # q = mp.Queue()
    db_client = pymongo.MongoClient()
    # p1 = mp.Process(target = f, args = (q, 0))
    # p2 = mp.Process(target = writer, args = (100, ))
    # p3 = mp.Process(target = writer2, args = (100, ))
    # # p1.start()
    # p2.start()
    # p3.start()
    # p3.join()
    # # p1.join()
    # p2.join()
    conclude_interval_TRADES_wrapper(db_client, "AMD")
    conclude_interval_TRADES_wrapper(db_client, "BABA")
    conclude_interval_TRADES_wrapper(db_client, "NVDA")



if __name__ == "__main__":
    run_main()
"""
