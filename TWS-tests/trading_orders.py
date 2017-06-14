import sys

import ibapi.order_condition
from ibapi.order import (OrderComboLeg, Order)
from ibapi.common import *
from ibapi.tag_value import TagValue
from ibapi import order_condition
from ibapi.order_condition import *


class CreateTradingOrders:
    """
    Market order are orders buy or sell at market current prices.

    >>> Products: BOND, CFD, EFP, CASH, FOUND, FUT, FOP, OPT, STK, WAR
    """
    @staticmethod
    def create_market_order(action: str, quantity: float):
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity

        return order

    
