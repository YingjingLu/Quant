import pymongo
import pprint
import datetime
from bson.objectid import ObjectId


def mongo_insert_historical(req_id, query_dict, collection, date: str, _open: float, high: float,
                   low: float, close: float, volume: int, barCount: int,
                   WAP: float, hasGaps: int):

    total_list = date.split(" ")
    yr = int(total_list[0][0:4])
    mo = int(total_list[0][4:6])
    dy = int(total_list[0][6:8])
    # if the data is daily, monthly, yearly
    if (len(total_list) == 1):
        converted = datetime.datetime(yr,mo,dy)
    else:
        time_list = total_list[2].split(":")
        converted = datetime.datetime(yr,mo,dy,int(time_list[0]), int(time_list[1]), int(time_list[2]))
    post = {
            "date" : converted,
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

def mongo_insert_historical(req_id, query_dict, collection, date: str, _open: float, high: float,
                   low: float, close: float, volume: int, barCount: int,
                   WAP: float, hasGaps: int):

    total_list = date.split(" ")
    yr = int(total_list[0][0:4])
    mo = int(total_list[0][4:6])
    dy = int(total_list[0][6:8])
    # if the data is daily, monthly, yearly
    if (len(total_list == 1)):
        converted = datetime.datetime(yr,mo,dy)
    else:
        time_list = total_list[2].split(":")
        converted = datetime.datetime(yr,mo,dy,int(time_list[0]), int(time_list[1]), int(time_list[2]))
    post = {
            "date" : converted,
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
