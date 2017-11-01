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
import config as cfg
import trade as td

transl0 = td.Translator()

def auth():
    accountID, token = None, None
    with open("./oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

accountID, access_token = auth()

cfg.brokerList = {'oanda': {'token': access_token, 'account': accountID}}
cfg.pairList = []

client= API(access_token = cfg.brokerList['oanda']['token'])
r = trades.OpenTrades(accountID = accountID)
client.request(r)
reply = dict(r.response)
tList = reply["trades"]
tList.reverse()

posList = []
for T in tList:
    ro = trades.TradeDetails(accountID = cfg.brokerList['oanda']['account'], tradeID = T["id"])
    client.request(ro)
    reply = dict(ro.response)
    oT = reply["trade"]
    if not oT["instrument"] in cfg.pairList:
        cfg.pairList.append(oT["instrument"])
        cfg.pairList.sort()
    print(oT)
    if float(oT["initialUnits"]) >= 0:
        typePos = 'l'
    else:
        typePos = 's'
    posList.append(td.Position('oanda', accountID, oT["id"], oT["instrument"], float(oT["price"]), abs(float(oT["initialUnits"])), typePos, pd.Timestamp(oT["openTime"])))
    posList[-1].status = 'o'
    if "closingTransactionIDs" in oT.keys():
        for cT in oT["closingTransactionIDs"]:
            rc = trans.TransactionDetails(accountID = accountID, transactionID = cT)
            client.request(rc)
            replyt = dict(rc.response)
            if "tradeReduced" in replyt["transaction"].keys():
                oRe = replyt["transaction"]["tradeReduced"]
                v = posList[-1].log.iloc[-1,].vol - abs(float(oRe["units"]))
                p = replyt["transaction"]["price"]
                cp = float(oRe["realizedPL"])
                t = pd.Timestamp(replyt["transaction"]["time"])
                posList[-1].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp}

parstreamtrans =\
    {
        "instruments": ",".join(cfg.pairList)
    }

rec = 0
pstream = pricing.PricingStream(accountID=cfg.brokerList['oanda']['account'], params=parstreamtrans)
psv = client.request(pstream)
tstream = trans.TransactionsStream(accountID = cfg.brokerList['oanda']['account'])
tsv = client.request(tstream)
while True:
    oP = dict(psv.__next__())
    print(json.dumps(oP, indent=4))
    oT = dict(tsv.__next__())
    print(json.dumps(oT, indent=4))
    if oT["type"] == "ORDER_FILL":
        if "tradeOpened" in oT.keys():
            oC = oT["tradeOpened"]
            tempL = [o for o in posList if o.posID == oC["id"]]
            if tempL == []:
                if not oT["instrument"] in cfg.pairList:
                    cfg.pairList.append(oC["instrument"])
                    cfg.pairList.sort()
                print(oC)
                if float(oC["initialUnits"]) >= 0:
                    typePos = 'l'
                else:
                    typePos = 's'
                posList.append(td.Position('oanda', accountID, oC["id"], oC["instrument"], float(oC["price"]),
                                           abs(float(oC["initialUnits"])), typePos, pd.Timestamp(oC["openTime"])))
                posList[-1].status = 'o'
        if "tradesClosed" in oT.keys():
            oCl = oT["tradesClosed"]
            oCl.reverse()
            for ocp in oCl:
                iL = [j for j in range(posList.__len__()) if posList[j].posID == ocp["tradeID"]]
                i = int(iL[0])
                v = posList[i].log.iloc[-1,].vol - abs(float(ocp["units"]))
                p = oT["price"]
                cp = float(ocp["realizedPL"])
                t = pd.Timestamp(oT["time"])
                posList[i].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp}
                if posList[i].log.loc[t].vol == 0:
                    posList[i].status = 'c'
        if "tradeReduced" in oT.keys():
            oRe = oT["tradeReduced"]
            iL = [j for j in range(posList.__len__()) if posList[j].posID == oRe["tradeID"]]
            i = int(iL[0])
            v = posList[i].log.iloc[-1,].vol - abs(float(oRe["units"]))
            p = oT["price"]
            cp = float(oT["tradeReduced"]["realizedPL"])
            t = pd.Timestamp(oT["time"])
            posList[i].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp}
            if posList[i].log.loc[t].vol == 0:
                posList[i].status = 'c'
    oP = dict(psv.__next__())
    print(json.dumps(oP, indent=4))
    rec += 1
    # if rec == 3:
    #     posList[-1].closePos(10)
    if rec >=10 :
        break
