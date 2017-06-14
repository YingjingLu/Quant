


#
import sys
import ibapi.order_condition
from ibapi.order import (OrderComboLeg, Order)
from ibapi.common import *
from ibapi.tag_value import TagValue
from ibapi import order_condition
from ibapi.order_condition import *

class OrderCreateMethods:

    @staticmethod
    def MKT_order(action, quantity):
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity

    @staticmethod
    def LMT_order(action, quantity, price):
        order = Order()
        order.action = action
        order.orderType = "LMT"
        order.lmtPrice = price
        order.totalQuantity = quantity
