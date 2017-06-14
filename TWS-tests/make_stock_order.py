#################### Globals #################################
BUY_ACTION = "BUY"
SELL_ACTION = "SELL"
DEFAULT_ORDER_ACTION = BUY_ACTION
MARKET_ACTION = "MKT"
LIMIT_ACTION = "LMT"
STOP_ACTION = "STP"
DEFAULT_ORDER_TYPE = MARKET_ACTION #[ MKT, LMT, STP]

STOCK_ORDER_ID = 0 # !!! need to be fixed!!!
##################### End Globals ##############################
import sys
from ibapi.common import *
from ibapi.order_condition import *
from ibapi.contract import *
from ibapi.order import *
from ibapi.order_state import *
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_report import CommissionReport
from ibapi.contract import *

################ custom model import ###############################
from trading_contracts.ContractCreateMethods import create_US_stock_contract
################# End custom model import ##########################

def create_order(action = DEFAULT_ORDER_ACTION,
                 quantity = None,
                 price = None,
                 order_type = DEFAULT_ORDER_TYPE,
                 ):
    if quantity == None:
        print("Please Enter a quantity for STK order")
        return None
    else if quantity % 100 != 0:
        print("Order quantity should be multiple of 100")
        return None
    else:
        order = Order()
        order.orderId = ORDER_ID
        order.totalQuantity = quantity
        order.action = action
        print(" !! creating a %s order of STK" % action)
        if order.action == LIMIT_ACTION:
            order.lmtPrice = price
    return order
