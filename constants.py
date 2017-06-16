class UTIL_CST:
    NUM_TRADE_PRODUCT = 3

class STK_CST:
    BUY = 1
    SELL = -1

class Query_CST:
    STK_HISTORY_WHAT_TO_DO_LIST = [
                               "TRADES",
                               "MIDPOINT",
                               "BID",
                               "ASK",
                               "BID_ASK",
                               ]
    STK_HISTORY_BAR_SIZE = [
                            "5sec",
                            "10secs",
                            "15secs",
                            "30secs",
                            "1min",
                            "2mins",
                            "3mins",
                            "5mins",
                            "10mins",
                            "15mins",
                            "20mins",
                            "30mins",
                            "1hour",
                            "2hours",
                            "3hours",
                            "4hours",
                            "8hours",
                            "1day",
                            "1week",
                            "1month"
                            ]



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
