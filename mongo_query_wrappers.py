import pymongo
import pprint
import datetime
from bson.objectid import ObjectId
from constants import QUERY_CST

INTERVAL_DICT = {
                    "S":[1, 5, 10, 15, 30],
                    "M":[1, 3, 5, 10, 20, 30],
                    "H":[1, 3],
                    "D":[1],
                    "MO":[1]
                }

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



def get_MA_collection(db, interval, unit, what_to_do, field):


    return None

def rt_MA(collection, interval, unit, field):
    pass

def MA(collection, interval, unit, field):
    collection_name = what_to_do + "_"
    is_builtin_interval = False
    total = 0
    key = ""
    bar_count = 0
    # if the interval request is builtin in databse
    if (interval in INTERVAL_DICT[unit]):
        collection_name += str(interval)
        is_builtin_interval = True

    # if it is not a built in interval in the collection,
    # find th best fit interval range
    else:
        pass


    if unit == "S":
        collection_name += "sec"
    elif unit == "M":
        collection_name += "min"
    elif unit == "H":
        collection_name += "hour"
    elif unit == "D":
        collection_name += "day"
    elif unit == "Mo":
        collection_name += "month"
    else:
        raise_local_error("undefined unit", "MA")
        return
        # check if the field is valid
    if ("P"):
        key = "price"
    elif (field == "V" and field != "TRADES"):
        railse_local_error("Volumn should request TRADES", "MA")
        return
    elif (field == "V"):
        key = "volume"
    else:
        raise_local_error("undefined field", "MA")
        return

    if is_builtin_interval:
        posts = collection.find().sort({"date":pymongo.DESCENDING}).limit(interval)
        for post in posts:
            total += post[key]
        bar_count = interval
    else:
        pass

    return total / bar_count

def symbol_to_db_name(symbol: str):
    return "STK_" + symbol

def req_barsize_to_db_barsize(req_barsize: str):
    return QUERY_CST.TO_DB_BAR_SIZE_DICT[req_barsize]


def convert_collection_name(what_to_do: str, bar_size: str):
    return what_to_do + "_" + req_barsize_to_db_barsize(bar_size)


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
    _iter = collection.find().sort("datetime", pymongo.ASCENDING).limit(1)
    for obj in _iter:
        return obj["datetime"]

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
