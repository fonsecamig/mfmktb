import numpy as np
import pandas as pd
import trade as td
import strategies as stratg
import json
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

transl.initAccount('oanda', access_token)

for pair in cfg.pairList:
    htab = transl.histPrice('oanda', 0, 'EUR_USD', pd.Timestamp('2016-01-01T00:00:00'), gran='S5')
    htab.to_csv(pair + ".csv")