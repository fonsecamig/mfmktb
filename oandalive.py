import json

from oandapyV20.contrib.requests import (
    MarketOrderRequest,
    TakeProfitDetails,
    StopLossDetails
)

import oandapyV20.endpoints.orders as orders
import oandapyV20

def exampleAuth():
    accountID, token = None, None
    with open("account.txt") as I:
        accountID = I.readline()
        token = I.readline()
    return accountID, token

