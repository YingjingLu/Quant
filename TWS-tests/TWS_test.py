import sys
import argparse
import datetime
import collections
import inspect

import logging
import time
import os.path


from ibapi import wrapper
from ibapi.client import EClient
from ibapi.utils import iswrapper

# types
from ibapi.common import *
from ibapi.order_condition import *
from ibapi.contract import *
from ibapi.order import *
from ibapi.order_state import *
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_report import CommissionReport
from ibapi.scanner import ScannerSubscription
from ibapi.ticktype import *

from ibapi.account_summary_tags import *
from ContractSamples import ContractSamples

class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

class TestApp(wrapper.EWrapper, TestClient):
    def __init__(self):
        wrapper.EWrapper.__init__(self)
        TestClient.__init__(self, wrapper = self)


    def streamAMD(self):
        self.reqMktDepth(2101, ContractSamples.USStock(), 5, [])





def main():
    app = TestApp()
    app.connect("127.0.0.1", 7497, 999)
    app.run()
    app.disconnect()

main()
