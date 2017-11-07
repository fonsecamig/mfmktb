import numpy as np
import pandas as pd
import datetime as dt
import json
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.transactions as trans
import oandapyV20.endpoints.pricing as pricing
import trade as td
import config as cfg

def auth():
    accountID, token = None, None
    with open("./oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

accountID, access_token = auth()

cfg.pairList = ["EUR_USD"]

cfg.transl.initAccount('oanda', access_token)

rec = 0
cfg.transl.initPosLog('oanda', 0)
cfg.transl.initTick('oanda', 0)
print(cfg.priceList['oanda'][0])
while True:
    cfg.transl.tick('oanda', 0)
    cfg.transl.updatePosLog('oanda', 0)
    print(cfg.priceList['oanda'][0])
    rec += 1
    if rec >=10 :
        break
