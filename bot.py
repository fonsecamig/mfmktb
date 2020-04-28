import numpy as np
import pandas as pd
import trade as td
import strategies as stratg
import json
import requests
import urllib3
import config as cfg


def auth():
    accountID, token = None, None
    with open("./oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token


accountID, access_token = auth()

transl = td.Translator()

cfg.pairList = ["EUR_USD", "GBP_USD"]
strategy = stratg.TestStrategy(volTest=1000, slip=.01, perProfit=.00025, perLoss=.5)
dur = pd.Timedelta(days=7)

transl.initAccount('oanda', access_token)
# cfg.brokerList['oanda'] = cfg.brokerList['oanda'][0]

for broker in cfg.brokerList:
    for acc in range(cfg.brokerList[broker]['accounts'].__len__()):
        transl.initTick(broker, acc)
        transl.initPosLog(broker, acc)

strategy.initiate()
timeStop = pd.Timestamp.now(tz='utc') + dur
while pd.Timestamp.now(tz='utc') <= timeStop:
    for broker in cfg.brokerList:
        for acc in range(cfg.brokerList[broker]['accounts'].__len__()):
            try:
                transl.tick(broker, acc)
                print(pd.Timestamp.now())
                print(cfg.priceList[broker]['accounts'][acc])
                print([(p.log, p.status) for p in cfg.posList])
                print(strategy.advice())
                transl.execute(strategy.advice())
            except (ConnectionResetError, urllib3.exceptions.ProtocolError, requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError, requests.exceptions.HTTPError,
                    requests.exceptions.ChunkedEncodingError):
                transl.initPosLog(broker, acc)
                transl.initTick(broker, acc)

posLogL = pd.DataFrame([p.log for p in cfg.posList])
posLog = pd.concat(posLogL, keys=list(range(1, posLogL.__len__() + 1)))
with pd.ExcelWriter('positions.xlsx') as outfile:
    posLog.to_excel(outfile)

brokerL = []
bIndex = []
ind = 0
for broker in cfg.brokerList:
    for acc in range(cfg.brokerList[broker]['accounts'].__len__()):
        brokerL.append(cfg.brokerList[broker][acc].log)
        bIndex.append((ind + 1, acc + 1))
    ind += 1
index = pd.MultiIndex.from_tuples(bIndex, names=['broker', 'account'])
brokerLog = pd.concat(brokerL, keys=index)
with pd.ExcelWriter('accounts.xlsx') as outfile:
    brokerLog.to_excel(outfile)
