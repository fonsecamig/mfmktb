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
import strategies as stratg
import config as cfg

def auth():
    accountID, token = None, None
    with open("./oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

accountID, access_token = auth()

transl = td.Translator()

cfg.pairList = ["EUR_USD", "GBP_USD", "USD_CAD", "GBP_CHF"]
strategy = stratg.TestStrategy(10, 0.00001, 0.00025, 0.5)
transl.initAccount('oanda', access_token)

rec = 0
transl.initPosLog('oanda', 0)
transl.initTick('oanda', 0)
while True:
    transl.tick('oanda', 0)
    print([(p.log, p.status) for p in cfg.posList])
    print(strategy.advice())
    transl.execute(strategy.advice())
    transl.updatePosLog('oanda', 0)
    rec += 1
    if rec >=100 :
        break
