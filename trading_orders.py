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
        return order

    @staticmethod
    def LMT_order(action, quantity, price):
        order = Order()
        order.action = action
        order.orderType = "LMT"
        order.lmtPrice = price
        order.totalQuantity = quantity
        return order


    @staticmethod
    def PriceCondition(triggerMethod:int, conId:int, exchange:str, price:float,
                        isMore:bool, isConjunction:bool):

        #! [price_condition]
        #Conditions have to be created via the OrderCondition.create
        priceCondition = order_condition.Create(OrderCondition.Price)
        #When this contract...
        priceCondition.conId = conId
        #traded on this exchange
        priceCondition.exchange = exchange
        #has a price above/below
        priceCondition.isMore = isMore
        priceCondition.triggerMethod = triggerMethod
        #this quantity
        priceCondition.price = price
        #AND | OR next condition (will be ignored if no more conditions are added)
        priceCondition.isConjunctionConnection = isConjunction
        #! [price_condition]
        return priceCondition


    @staticmethod
    def ExecutionCondition(symbol:str, secType:str, exchange:str,
                           isConjunction:bool):

        #! [execution_condition]
        execCondition = order_condition.Create(OrderCondition.Execution)
        #When an execution on symbol
        execCondition.symbol = symbol
        #at exchange
        execCondition.exchange = exchange
        #for this secType
        execCondition.secType = secType
        #AND | OR next condition (will be ignored if no more conditions are added)
        execCondition.isConjunctionConnection = isConjunction
        #! [execution_condition]
        return execCondition


    @staticmethod
    def MarginCondition(percent:int, isMore:bool, isConjunction:bool):

        #! [margin_condition]
        marginCondition = order_condition.Create(OrderCondition.Margin)
        #If margin is above/below
        marginCondition.isMore = isMore
        #given percent
        marginCondition.percent = percent
        #AND | OR next condition (will be ignored if no more conditions are added)
        marginCondition.isConjunctionConnection = isConjunction
        #! [margin_condition]
        return marginCondition


    @staticmethod
    def PercentageChangeCondition(pctChange:float, conId:int, exchange:str,
                                  isMore:bool, isConjunction:bool):

        #! [percentage_condition]
        pctChangeCondition = order_condition.Create(OrderCondition.PercentChange)
        #If there is a price percent change measured against last close price above or below...
        pctChangeCondition.isMore = isMore
        #this amount...
        pctChangeCondition.changePercent = pctChange
        #on this contract
        pctChangeCondition.conId = conId
        #when traded on this exchange...
        pctChangeCondition.exchange = exchange
        #AND | OR next condition (will be ignored if no more conditions are added)
        pctChangeCondition.isConjunctionConnection = isConjunction
        #! [percentage_condition]
        return pctChangeCondition


    @staticmethod
    def TimeCondition(time:str, isMore:bool, isConjunction:bool):

        #! [time_condition]
        timeCondition = order_condition.Create(OrderCondition.Time)
        #Before or after...
        timeCondition.isMore = isMore
        #this time..
        timeCondition.time = time
        #AND | OR next condition (will be ignored if no more conditions are added)
        timeCondition.isConjunctionConnection = isConjunction
        #! [time_condition]
        return timeCondition


    @staticmethod
    def VolumeCondition(conId:int, exchange:str, isMore:bool, volume:int,
                        isConjunction:bool):

        #! [volume_condition]
        volCond = order_condition.Create(OrderCondition.Volume)
        #Whenever contract...
        volCond.conId = conId
        #When traded at
        volCond.exchange = exchange
        #reaches a volume higher/lower
        volCond.isMore = isMore
        #than this...
        volCond.volume = volume
        #AND | OR next condition (will be ignored if no more conditions are added)
        volCond.isConjunctionConnection = isConjunction
        #! [volume_condition]
        return volCond
