import pymongo
import pprint
import datetime
from bson.objectid import ObjectId
from mongo_query_wrappers import *
from general_util import *
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
def conclude_interval_TRADES(prev_collection, collection, start_dt, end_dt, log_file):
    print("Start Conclude From: ", start_dt, " To ", end_dt)
    query = prev_collection.find({"datetime": {"$gte": start_dt, "$lt": end_dt}}).sort("datetime", pymongo.DESCENDING)
    count = query.count()
    if  count == 0:
        print("Error: No Record ", prev_collection, " From: ", start_dt, " To: ", end_dt, "Has no result")
        log_file.write("No Record to Insert to " + str(prev_collection) + " From " + str(start_dt)+ " To " + str(end_dt) + "\n")
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
    print("Finish Conclude From: ", start_dt, " To ", end_dt)
    print(">>> Result Dict: ")
    pprint.pprint(result_dict)
    collection.insert_one(result_dict)
    if total_hasGaps:
        log_file.write("Missing Record Insert to " + str(collection), + " From " + str(start_dt)+ " To " + str(end_dt) + "\n")


def conclude_interval_TRADES_1_day(collection, bar_size, dt):
    ask_year = dt.year
    ask_month = dt.month
    ask_day = dt.day

    start_dt = datetime.datetime(ask_year, ask_month, ask_day, 9, 30, 0)
    end_dt = datetime.datetime(ask_year, ask_month, ask_day, 16, 0, 0)

    dt = start_dt

    while dt < end_dt:
        delta_dt = dt + QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[bar_size]
        collection.insert_one(conclude_interval_TRADES(collection, dt, delta_dt))



def conclude_interval_TRADES_wrapper(db_client, symbol, log_file):
    db = db_client[symbol_to_db_name(symbol)]
    log_file.write("Enter DB: " +symbol_to_db_name(symbol) + "\n")
    bar_size_list = QUERY_CST.DB_AVAILABLE_BAR_SIZE_LIST
    for bar_size_index in range(1, len(bar_size_list)):

        prev_bar_size = bar_size_list[bar_size_index - 1]
        bar_size = bar_size_list[bar_size_index]

        prev_collection =db[convert_collection_name("TRADES", prev_bar_size)]
        collection = db[convert_collection_name("TRADES", bar_size)]
        log_file.write("In Collection: " + convert_collection_name("TRADES", bar_size) + "\n")
        log_file.write("Prev Collection: " + convert_collection_name("TRADES", prev_bar_size) + "\n")

        # update_start_dt------cur_start_dt////////////cur_end_dt-------update_end_dt

        update_start_dt = find_whole_start_dt(prev_collection, bar_size)
        update_end_dt = find_whole_end_dt(prev_collection, prev_bar_size, bar_size)

        log_file.write("Prev Collection Start: " + str(find_whole_start_dt(prev_collection, bar_size)) + "\n")
        log_file.write("Prev Collection End: " + str(find_whole_end_dt(prev_collection, prev_bar_size, bar_size)) + "\n")

        delta = QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[bar_size]
        log_file.write("Delta" + str(delta) + "\n")

        if prev_collection.find_one() == None:
            print("Error, not building up for previous collection in >> conclude_interval_TRADES_wrapper")
            return

        if collection.find_one() == None:
            first_time = 1
            while(update_start_dt < update_end_dt):
                conclude_interval_TRADES(prev_collection, collection, update_start_dt, update_start_dt + delta, log_file)
                if first_time == 1:
                    collection.create_index([("datetime", pymongo.DESCENDING)])
                    first_time = 0
                update_start_dt += delta
                if not is_in_STK_Trading_hour(update_start_dt):
                    update_start_dt = STK_next_trade_day(update_start_dt)
            log_file.write("First time collection: " + convert_collection_name("TRADES", bar_size) + "Finishes" + "\n")
        else:
            cur_start_dt = earlest_datetime(collection)
            cur_end_dt = most_current_datetime(collection) + delta

            while (update_start_dt < cur_start_dt):
                conclude_interval_TRADES(prev_collection, collection, update_start_dt, delta + update_start_dt, log_file)
                update_start_dt += delta

                if not is_in_STK_Trading_hour(update_start_dt):
                    update_start_dt = STK_next_trade_day(update_start_dt)

            while(cur_end_dt < update_end_dt):
                conclude_interval_TRADES(prev_collection, collection, cur_end_dt, cur_end_dt + delta, log_file)
                cur_end_dt += delta
                if not is_in_STK_Trading_hour(cur_end_dt):
                    cur_end_dt = STK_next_trade_day(cur_end_dt)
    print(symbol, " Finishes")
