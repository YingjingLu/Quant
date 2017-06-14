import datetime


def parse_date(date):
    pass

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
