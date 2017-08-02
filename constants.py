import datetime

class UTIL_CST:
    NUM_TRADE_PRODUCT = 3
    LOG_OPERATION_TYPE = {"insert", "update", "delete","read"}

class STK_CST:
    BUY = 1
    SELL = -1

class QUERY_CST:
    STK_HISTORY_WHAT_TO_DO_LIST = [
                               "TRADES"
                            #    "MIDPOINT",
                            #    "BID",
                            #    "ASK",
                            #    "BID_ASK",
                               ]
    STK_HISTORY_WHAT_TO_DO_SET = {
                               "TRADES",
                               "MIDPOINT",
                               "BID",
                               "ASK",
                               "BID_ASK",
                               }
    HISTORY_BAR_SIZE_DICT = {
                            "5 secs": "3600 S"
                            # "10 secs" : "14400 S",
                            # "15 secs": "14400 S",
                            # "30 secs": "28800 S",
                            # "1 min": "1 D",
                            # "2 mins": "2 D",
                            # "3 mins": "2 D",
                            # "5 mins": "2 D",
                            # "10 mins": "2 D",
                            # "15 mins": "2 D",
                            # "20 mins": "1 W",
                            # "30 mins": "1 W",
                            # "1 hour": "1 M",
                            # "2 hours": "1 M",
                            # "3 hours": "1 M",
                            # "4 hours": "1 M",
                            # "8 hours": "1 M",
                            # "1 day": "1 Y",
                            # "1 week": "1 Y",
                            }
    TO_DB_BAR_SIZE_DICT = {
                            "5 secs": "5secs",
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
    DB_AVAILABLE_BAR_SIZE_LIST = [
                            "5 secs",
                            "10 secs",
                            "15 secs",
                            "30 secs",
                            "1 min",
                            "2 mins",
                            "3 mins",
                            "5 mins",
                            "10 mins",
                            "15 mins",
                            "20 mins",
                            "30 mins",
                            "1 day"

    ]
    BAR_SIZE_TO_TIMEDELTA_DICT = {
                            "5 secs": datetime.timedelta(seconds = 5),
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
                            "1 week": datetime.timedelta(weeks = 1)
    }
    GET_RECORD_INTERVAL = {
                            "5 secs": datetime.timedelta(seconds = 3600),
                            "10 secs": datetime.timedelta(seconds = 14400),
                            "15 secs": datetime.timedelta(seconds = 14400),
                            "30 secs": datetime.timedelta(seconds = 28800),
                            "1 min": datetime.timedelta(days = 1),
                            "2 mins": datetime.timedelta(days = 1),
                            "3 mins": datetime.timedelta(days = 2),
                            "5 mins": datetime.timedelta(days = 3),
                            "10 mins": datetime.timedelta(days = 15),
                            "15 mins": datetime.timedelta(days = 20),
                            "20 mins": datetime.timedelta(days = 20),
                            "30 mins": datetime.timedelta(days = 20),
                            "1 hour": datetime.timedelta(days = 30),
                            "2 hours": datetime.timedelta(days = 60),
                            "3 hours": datetime.timedelta(days = 90),
                            "4 hours": datetime.timedelta(days = 120),
                            "8 hours": datetime.timedelta(days = 240),
                            "1 day": datetime.timedelta(days = 360)
    }
    RT_BAR_BAR_SIZE_TO_SEC = {
                                "5 secs": 5,
                                "10 secs": 10,
                                "15 secs": 15,
                                "30 secs": 30,
                                "1 min": 60,
                                "2 mins": 120,
                                "3 mins": 180,
                                "5 mins": 300,
                                "10 mins": 600,
                                "15 mins": 900,
                                "20 mins": 1200,
                                "30 mins": 1800,
                                "1 hour": 3600,
                                "2 hours": 7200,
                                "3 hours": 10800,
                                "4 hours": 14400,
                                "8 hours": 28800
    }




    HISTORY_REQ_1 = 4004

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

class MKT_TICK_TYPES:
    WRAPPER_TYPE = {
                        0: "tickPrice",
                        1: "tickSize",
                        2: "tickString",
                        3: "tickGeneric"
    }

    TICK_TYPE = {
                    0:{
                        1: "HIghest price bid for the contract",
                        2: "Lowest ask price",
                        4: "Last price traded",
                        6: "Highest price for the day",
                        7: "Lowest price for the day",
                        9: "Last available closing price of privious day",
                        14: "Open price today",
                        15: "Lowest price last 13 weeks",
                        16: "Highest pric last 13 weeks",
                        17: "lowest price in last 26 weeks",
                        18: "Highest in 26 weeks",
                        19: "Lowest in 52 weeks",
                        20: "Highest in 52 weeks",
                        35: "potential auction price",
                        37: "Current theortical calculated price",
                        50: "Yield for bond at current bid price",
                        51: "Yield for bond at current ask price",
                        52: "Implied Yield for bond at last price",
                        57: "Last regular hour trade price"
                    },

                    1:{
                        0: "number of contract at bid price",
                        3: "number of contracts at ask price",
                        5: "number of contract traded at last price",
                        8: "today's comulated volume  // 100",
                        21: "90 days average volume // 100",
                        27: "Call option open interest",
                        28: "Put option open interest",
                        29: "Call option volume for trading day",
                        30: "Put option volume for the trading day",
                        34: "The number of shares that would trade if auction held now",
                        36: "number of unmatched shares of auction",
                        63: "The past three minutes volume. Interpolation may be applied.",
                        64: "The past five minutes volume. Interpolation may be applied.",
                        65: "The past ten minutes volume. Interpolation may be applied."
                    },

                    2:{
                        32: "Bid exchange",
                        33: "Ask exchange",
                        45: "time of last trade",
                        47: "reuter's fundamental ratio",
                        48: "rt volume",
                        59: "IB dividend",
                        77: "RT trade volume"
                    },

                    3:{
                        23: "30 day historical volatility"

                    }





    }
