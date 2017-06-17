import pymongo
import pprint
import datetime
from bson.objectid import ObjectId
from mongo_query_wrapper import *
from general_util import *

def mongo_insert_historical(collection, date: str, _open: float, high: float,
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
        print("post -> ")
        print(post)
        collection.insert_one(post)
        print("finished insert in collection")
    else:
        print("Record Exists")

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
