import numpy as np
import pandas as pd
import datetime as dt
import json
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.transactions as trans
import trade as td

transl0 = td.Translator()

def auth():
    accountID, token = None, None
    with open("./oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

accountID, access_token = auth()

brokerList = {'oanda': {'token': access_token, 'account': accountID}}
client = API(access_token = brokerList['oanda']['token'])

pairList = []

r = trades.OpenTrades(accountID = accountID)
client.request(r)
reply = dict(r.response)
tList = reply["trades"]
tList.reverse()

posList = []
for T in tList:
    ro = trades.TradeDetails(accountID = brokerList['oanda']['account'], tradeID = T["id"])
    client.request(ro)
    reply = dict(ro.response)
    oT = reply["trade"]
    if not oT["instrument"] in pairList:
        pairList.append(oT["instrument"])
        pairList.sort()
    print(oT)
    if float(oT["initialUnits"]) >= 0:
        typePos = 'l'
    else:
        typePos = 's'
    posList.append(td.Position('oanda', accountID, oT["id"], oT["instrument"], float(oT["price"]), abs(float(oT["initialUnits"])), typePos, pd.Timestamp(oT["openTime"])))
    posList[-1].status = 'o'
    if "closingTransactionIDs" in oT.keys():
        for cT in oT["closingTransactionIDs"]:
            rc = trades.TradeDetails(accountID=accountID, tradeID=cT)
            client.request(rc)
            replyt = dict(rc.response)
            if "orderFillTransaction" in replyt.keys():
                oC = replyt["orderFillTransaction"]
                print(oC)
                v = posList[-1].log.iloc[-1,].vol - abs(float(oC["units"]))
                p = float(oC["price"])
                cp = float(oC["pl"])
                t = pd.Timestamp(oC["time"])
                posList[-1].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp}

# parstreamtrans =\
#     {
#         "instruments": "EUR_USD,EUR_JPY"
#     }

tstream = trans.TransactionsStream(accountID = brokerList['oanda']['account'])
tsv = client.request(tstream)
try:
    for T in tstream.response:  # or rv ...
        print(T)
        oT = dict(T)
        if "orderFillTransaction" in oT.keys():
            oF = oT["orderFillTransaction"]
            if "tradeOpened" in oF.keys():
                oC = oF["tradeOpened"]
                tempL = [o for o in posList if o.posID == oC["id"]]
                if tempL == []:
                    if not oT["instrument"] in pairList:
                        pairList.append(oC["instrument"])
                        pairList.sort()
                    print(oC)
                    if float(oC["initialUnits"]) >= 0:
                        typePos = 'l'
                    else:
                        typePos = 's'
                    posList.append(td.Position('oanda', accountID, oC["id"], oC["instrument"], float(oC["price"]),
                                               abs(float(oC["initialUnits"])), typePos, pd.Timestamp(oC["openTime"])))
                    posList[-1].status = 'o'
            if "tradesClosed" in oF.keys():
                oCl = oF["tradesClosed"]
                oCl.reverse()
                for ocp in oCL:
                    i = [j for j in range(posList) if posList[j].posID == ocp["id"]][0]
                    v = posList[i].log.iloc[-1,].vol - float(ocp["units"])
                    p = oF["price"]
                    cp =
                    t = pd.Timestamp(oF["time"])
                    posList[i].log.loc[t] =
finally:
    pass