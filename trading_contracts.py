
####################### Globals ####################################
US_CURRENCY = "USD"
DEFAULT_EXCHANGE = "SMART"
TYPE_STOCK = "STK"

######################## End Globals #####################################



#################### System and API inports ####################
import sys
from ibapi.contract import *


#################### End System and API Imports #####################



class ContractCreateMethods:

    """ Usually, the easiest way to define a Stock/CASH contract is through
    these four attributes.  """

    @staticmethod
    def create_US_stock_contract(stock_symbol,
                                 sec_type = TYPE_STOCK,
                                 exchange = DEFAULT_EXCHANGE,
                                 currency = US_CURRENCY
                                 ):
        #! [stkcontract]
        contract = Contract()
        contract.symbol = stock_symbol
        contract.secType = sec_type
        contract.currency = currency
        #In the API side, NASDAQ is always defined as ISLAND in the exchange field
        contract.exchange = exchange
        #! [stkcontract]
        return contract
