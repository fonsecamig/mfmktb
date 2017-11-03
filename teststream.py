import numpy as np
import pandas as pd
import datetime as dt
import json
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.transactions as trans
import oandapyV20.endpoints.pricing as pricing
import trade as td
import config as cfg

transl0 = td.Translator()

def auth():
    accountID, token = None, None
    with open("./oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

accountID, access_token = auth()

cfg.brokerList = {'oanda': {'token': access_token, 'accounts': [accountID]}}
cfg.pairList = []
cfg.pairList, cfg.posList = cfg.transl.initPosLog('oanda', cfg.brokerList['oanda']['token'], cfg.brokerList['oanda']['accounts'][0], cfg.pairList, [])

client = API(access_token = cfg.brokerList['oanda']['token'])
tstream = trans.TransactionsStream(accountID = accountID)
cfg.brokerList['oanda']['tsv'] = client.request(tstream)
parstreamtrans =\
    {
        "instruments": ",".join(cfg.pairList)
    }
pstream = pricing.PricingStream(accountID = accountID, params = parstreamtrans)
cfg.brokerList['oanda']['psv'] = client.request(pstream)

rec = 0
pstream = pricing.PricingStream(accountID=cfg.brokerList['oanda']['account'], params=parstreamtrans)
psv = client.request(pstream)
tstream = trans.TransactionsStream(accountID = cfg.brokerList['oanda']['account'])
tsv = client.request(tstream)

while True:
    oP = dict(psv.__next__())
    print(json.dumps(oP, indent=4))
    rec += 1
    # if rec == 3:
    #     posList[-1].closePos(10)
    if rec >=10 :
        break
