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
