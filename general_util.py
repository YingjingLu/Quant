import datetime
from constants import *

def parse_datetime(dt):
    total_list = dt.split(" ")
    yr = int(total_list[0][0:4])
    mo = int(total_list[0][4:6])
    dy = int(total_list[0][6:8])
    # if the data is daily, monthly, yearly
    if (len(total_list) == 1):
        converted = datetime.datetime(yr,mo,dy)
    else:
        time_list = total_list[2].split(":")
        converted = datetime.datetime(yr,mo,dy,int(time_list[0]), int(time_list[1]), int(time_list[2]))

    return converted


def incr_weekday(weekday):
    if(weekday > 7 or weekday < 1):
        print("WRONG WEEKDAY")
        return
    if weekday == 7:
        return 1
    else:
        weekday += 1
        return weekday

def decr_weekday(weekday):
    if(weekday > 7 or weekday < 1):
        print("WRONG WEEKDAY")
        return
    if weekday == 1:
        return 7
    else:
        weekday -= 1
        return weekday

def calc_timedelta(bar_size: str):
    if bar_size == "1 month":
        print("No timedelta for 1 month")
        return
    return QUERY_CST.BAR_SIZE_TO_TIMEDELTA_DICT[bar_size]

def bar_size_to_step_size(bar_size: str):
    return QUERY_CST.HISTORY_BAR_SIZE_DICT[bar_size]

def STK_next_trade_day(dt):
    d = dt.weekday()
    year = dt.year
    month = dt.month
    day = dt.day
    out = datetime.datetime(year, month, day, 9, 30, 0)
    if d == 4:
        return out + datetime.timedelta(days = 3)
    elif d == 5:
        return out + datetime.timedelta(days = 2)
    else :
        return out + datetime.timedelta(days = 1)

def STK_prev_trade_day_end(dt):
    d = dt.weekday()
    year = dt.year
    month = dt.month
    day = dt.day
    out = datetime.datetime(year, month, day, 16, 0, 0)
    if d == 0:
        return out - datetime.timedelta(days = 3)
    elif d == 6:
        return out - datetime.timedelta(days = 2)
    else:
        return out - datetime.timedelta(days = 1)


def is_in_STK_Trading_hour(dt):

    year = dt.year
    month = dt.month
    day = dt.day
    start = datetime.datetime(year, month, day, 9, 30, 0)
    end = datetime.datetime(year, month, day, 16, 0, 0)

    return start <= dt < end

def symbol_to_db_name(symbol: str):
    return "STK_" + symbol

def req_barsize_to_db_barsize(req_barsize: str):
    return QUERY_CST.TO_DB_BAR_SIZE_DICT[req_barsize]


def convert_collection_name(what_to_do: str, bar_size: str):
    return what_to_do + "_" + req_barsize_to_db_barsize(bar_size)

def convert_RT_collection_name(bar_size: str):
    return "RTBAR" + "_" + req_barsize_to_db_barsize(bar_size)
