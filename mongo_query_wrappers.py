import pymongo
import pprint
import datetime
from bson.objectid import ObjectId

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
