import datetime

class UTIL_CST:
    NUM_TRADE_PRODUCT = 3

class STK_CST:
    BUY = 1
    SELL = -1

class QUERY_CST:
    STK_HISTORY_WHAT_TO_DO_LIST = [
                               "TRADES",
                               "MIDPOINT",
                               "BID",
                               "ASK",
                               "BID_ASK",
                               ]
    STK_HISTORY_WHAT_TO_DO_SET = {
                               "TRADES",
                               "MIDPOINT",
                               "BID",
                               "ASK",
                               "BID_ASK",
                               }
    HISTORY_BAR_SIZE_DICT = {
                            "5 sec": "1 hr",
                            "10 secs" : "4 hrs",
                            "15 secs": "4 hrs",
                            "30 secs": "8 hrs",
                            "1 min": "1 D",
                            "2 mins": "2 D",
                            "3 mins": "2 D",
                            "5 mins": "2 D",
                            "10 mins": "2 D",
                            "15 mins": "2 D",
                            "20 mins": "1 W",
                            "30 mins": "1 W",
                            "1 hour": "1 M",
                            "2 hours": "1 M",
                            "3 hours": "1 M",
                            "4 hours": "1 M",
                            "8 hours": "1 M",
                            "1 day": "1 Y",
                            "1 week": "1 Y",
                            "1 month": "1 Y"
                            }
    TO_DB_BAR_SIZE_DICT = {
                            "5 sec": "5sec",
                            "10 secs": "10secs",
                            "15 secs": "15secs",
                            "30 secs": "30secs",
                            "1 min": "1min",
                            "2 mins": "2mins",
                            "3 mins": "3mins",
                            "5 mins": "5mins",
                            "10 mins": "10mins",
                            "15 mins": "15mins",
                            "20 mins": "20mins",
                            "30 mins": "30mins",
                            "1 hour": "1hour",
                            "2 hours": "2hours",
                            "3 hours": "3hours",
                            "4 hours": "4hours",
                            "8 hours": "8hours",
                            "1 day": "1day",
                            "1 week": "1week",
                            "1 month": "1month"
                           }
    BAR_SIZE_TO_TIMEDELTA_DICT{
                            "5 sec": datetime.timedelta(seconds = 5),
                            "10 secs": datetime.timedelta(seconds = 10),
                            "15 secs": datetime.timedelta(seconds = 15),
                            "30 secs": datetime.timedelta(seconds = 30),
                            "1 min": datetime.timedelta(minutes = 1),
                            "2 mins": datetime.timedelta(minutes = 2),
                            "3 mins": datetime.timedelta(minutes = 3),
                            "5 mins": datetime.timedelta(minutes = 5),
                            "10 mins": datetime.timedelta(minutes = 10),
                            "15 mins": datetime.timedelta(minutes = 15),
                            "20 mins": datetime.timedelta(minutes = 20),
                            "30 mins": datetime.timedelta(minutes = 30),
                            "1 hour": datetime.timedelta(hours = 1),
                            "2 hours": datetime.timedelta(hours = 2),
                            "3 hours": datetime.timedelta(hours = 3),
                            "4 hours": datetime.timedelta(hours = 4),
                            "8 hours": datetime.timedelta(hours = 8),
                            "1 day": datetime.timedelta(days = 1),
                            "1 week": datetime.timedelta(weeks = 1),
    }




    HISTORY_TRADES_1SEC_1 = 4001
    HISTORY_TRADES_5SEC_1 = 4002
    HISTORY_TRADES_10SEC_1 = 4003
    HISTORY_TRADES_15SEC_1 = 4004
    HISTORY_TRADES_30SEC_1 = 4005
    HISTORY_TRADES_1MIN_1 = 4006
    HISTORY_TRADES_2MIN_1 = 4007
    HISTORY_TRADES_3MIN_1 = 4008
    HISTORY_TRADES_5MIN_1 = 4009
    HISTORY_TRADES_10MIN_1 = 4010
    HISTORY_TRADES_15MIN_1 = 4011
    HISTORY_TRADES_20MIN_1 = 4012
    HISTORY_TRADES_30MIN_1 = 4013
    HISTORY_TRADES_1H_1 = 4014
    HISTORY_TRADES_2H_1 = 4015
    HISTORY_TRADES_3H_1 = 4016
    HISTORY_TRADES_4H_1 = 4017
    HISTORY_TRADES_8H_1 = 4018
    HISTORY_TRADES_1D_1 = 4019
    HISTORY_TRADES_1W_1 = 4020
    HISTORY_TRADES_1M_1 = 4021

    HEAD_TIMESTAMP_1 = 14001
class QUERY_HISTORY:
    HEAD_TIMESTANP_HISTORY = {
                                "AMD": 1,
                                "FB": 1,
                                "AAPL": 1,
                                "AMZN": 1,
                                "NVDA": 1,
                                "BABA": 1,
                                "WB": 1
                                }
