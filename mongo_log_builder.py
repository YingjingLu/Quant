import datetime
import pymongo
from general_util import *
from constants import *
from log_build_error_msg import *

# DB: STK_historical_data_build_log
#===============================================================================
"""
collection: <stk_symbol>: historical
  document:
            "what_to_do": "TRADES"....
            "bar_size": "5 secs" ....
            "start_dt":
            "end_dt":
            "result": True, False
            "insert_dt":
            "error_msg": None / MSG_INDEX
"""

def STK_historical_log_build(db_client, symbol: str, what_to_do: str,
                             bar_size: str, start_dt, end_dt, result: bool,
                             error_msg = None):

    if (bar_size not in QUERY_CST.DB_AVAILABLE_BAR_SIZE_LIST) and error_msg == None:
        result = False
        error_msg = STK_HISTORICAL_BUILD_ERROR[2]
    post = {
            "what_to_do": what_to_do,
            "bar_size": bar_size,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "result": result,
            "insert_dt": datetime.datetime.now(),
            "error_msg": error_msg
    }
    db_client["STK_historical_data_build_log"][symbol].insert_one(post)

"""
  collection: operation_log
  document:
          "operation_type": "insert", "update", "delete"
          "stk_symbol": "AMD"
          "bar_size":
          "start_date":
          "end_date":
          "result": "Success", "Fail"
          "operation_dt":
"""

def STK_historical_operation_log(operation_type, symbol, db_client, bar_size, start_date, end_date, result):

    post = {
            "operation_type": operation_type,
            "stk_symbol": symbol,
            "bar_size": bar_size,
            "start_date": start_date,
            "end_date": end_date,
            "result": result,
            "operation_dt": datetime.datetime.now()
    }
    db_client["STK_historical_data_build_log"]["operation_log"].insert_one(post)
