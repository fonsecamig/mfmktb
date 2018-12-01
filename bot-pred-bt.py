import os
import numpy as np
import pandas as pd
import trade as td
import strategies as stratg
import json
import requests
import config as cfg

transl = td.Translator()

# cfg.pairList = ["EUR_USD", "GBP_USD"]
# strategy = stratg.TestStrategy(10, 0.01, 0.00025, 0.5)
strategy = stratg.TestPredictionStrategy(10, 0.01, 0.00025, 0.5)
# dur = pd.Timedelta(seconds=5)

transl.initAccount('backtest', 0, btpath='/Users/fonsecamig/FXdata/raw/')

for broker in cfg.brokerList:
    for acc in range(cfg.brokerList[broker]['accounts'].__len__()):
        transl.initTick(broker, acc)
        transl.initPosLog(broker, acc)
        # print(cfg.priceList[broker]['accounts'][acc])

# strategy.initiate()
# timeStop = pd.Timestamp.now(tz='utc') + dur
online = True
while online:
    for broker in cfg.brokerList:
        for acc in range(cfg.brokerList[broker]['accounts'].__len__()):
                online = transl.tick(broker, acc)
                print(cfg.priceList[broker]['accounts'][acc])
                # print(cfg.history)
                # print([p.log for p in cfg.posList])
                # print(strategy.advice())
                # transl.execute(strategy.advice())
#
# posLogL = [p.log for p in cfg.posList]
# posLog = pd.concat(posLogL, keys=list(range(1, posLogL.__len__() + 1)))
# with pd.ExcelWriter('positions.xlsx') as outfile:
#     posLog.to_excel(outfile)
#
# brokerL = []
# bIndex = []
# ind = 0
# for broker in cfg.brokerList:
#     for acc in range(cfg.brokerList[broker]['accounts'].__len__()):
#         brokerL.append(cfg.brokerList[broker]['accounts'][acc]['log'])
#         bIndex.append((ind + 1, acc + 1))
#     ind += 1
# index = pd.MultiIndex.from_tuples(bIndex, names=['broker', 'account'])
# brokerLog = pd.concat(brokerL, keys=index)
# with pd.ExcelWriter('accounts.xlsx') as outfile:
#     brokerLog.to_excel(outfile)
