import pymongo
import pprint
import datetime
from bson.objectid import ObjectId
from constants import QUERY_CST
from general_util import *

# mvoing averages
"""
db: mongodatabase
interval: any int
unit: S, M, H, D, MO
what_to_do: TRADES, MIDPOINT, BID, ASK, BID_ASK
field: P:price, V:volume
"""

def raise_local_error(msg, func_name):
    print("Error: " + msg + "in func" + func_name + "@ mongo_query_wrappers")

def STK_bar_num_inclusive(db_client, start_dt, end_dt, symbol, bar_size):
    if(start_dt >= end_dt):
        print("Request Interval is invalid")
        return {"has_gap_count": 0, "bar_num": 0}
    db_name = symbol_to_db_name(symbol)
    collection_name = req_barsize_to_db_barsize(bar_size)
    query = db_client[db_name][collection_name].find(collection.find({"datetime": {"$gte": start_dt, "$lte": end_dt}}))
    has_gap_count = 0
    for q in query:
        if q["hasGaps"]:
            has_gap_count += 1

    return {"has_gap_count": has_gap_count, "bar_num": query.count()}

def get_stk_headtimestamp(db, symbol, what_to_do):
    result = db[symbol].find_one({"what_to_do": what_to_do})
    if result == None:
        print("No timestamp for this stock symbol: %s, what_to_do %s" % (symbol, what_to_do))
        return None
    pprint.pprint(result)
    return result["datetime"]

def datetime_exist(collection, dt):
    if  collection.find({"datetime": dt}).count() == 0:
        return False
    return True

def most_current_datetime(collection):
    return list(collection.find().sort("datetime", pymongo.DESCENDING).limit(1))[0]["datetime"]

def earlest_datetime(collection):
    return list(collection.find().sort("datetime", pymongo.ASCENDING).limit(1))[0]["datetime"]

def is_STK_full_day(collection, bar_size, dt):
    ask_year = dt.year
    ask_month = dt.month
    ask_day = dt.day

    gte = datetime.datetime(ask_year, ask_month, ask_day, 0, 0, 0)
    lt = datetime.datetime(ask_year, ask_month, ask_day, 23, 59, 59)

    dt_end = list(collection.find({"datetime": {"$gte": gte, "$lt": lt}}).sort("datetime", pymongo.DESCENDING).limit(1))[0]["datetime"]
    dt_start = list(collection.find({"datetime": {"$gte": gte, "$lt": lt}}).sort("datetime", pymongo.ASCENDING).limit(1))[0]["datetime"]

    ver_start_dt = datetime.datetime(ask_year, ask_month, ask_day, 9, 30, 0)
    ver_end_dt = datetime.datetime(ask_year, ask_month, ask_day, 16, 0, 0) - QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[bar_size]

    return (dt_end == ver_end_dt) and (dt_start == ver_start_dt)

def find_whole_start_dt(collection, bar_size):
    time_delta = QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[bar_size]

    start_dt = earlest_datetime(collection)
    ask_year = start_dt.year
    ask_month = start_dt.month
    ask_day = start_dt.day

    gte = datetime.datetime(ask_year, ask_month, ask_day, 9, 30, 0)
    lt = datetime.datetime(ask_year, ask_month, ask_day, 16, 0, 0)

    query = collection.find_one({"datetime": gte})
    while (query == None):
        gte = gte + time_delta
        query = collection.find_one({"datetime": gte})

    return query["datetime"]

def find_whole_end_dt(collection, collection_bar_size, ask_bar_size):
    ask_time_delta = QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[ask_bar_size]
    collection_time_delta = QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[collection_bar_size]

    start_dt = most_current_datetime(collection)
    ask_year = start_dt.year
    ask_month = start_dt.month
    ask_day = start_dt.day

    gte = datetime.datetime(ask_year, ask_month, ask_day, 9, 30, 0)
    lt = datetime.datetime(ask_year, ask_month, ask_day, 16, 0, 0)

    query = collection.find_one({"datetime": lt})
    if(ask_bar_size == "1 day"):
        if start_dt + collection_time_delta == lt:
            return lt
        else:
            return STK_prev_trade_day_end(lt)
    while (query == None):
        lt = lt - ask_time_delta
        query = collection.find_one({"datetime": lt})

    if (start_dt + collection_time_delta - ask_time_delta == query["datetime"]):
        return start_dt + collection_time_delta

    return query["datetime"]
