import numpy as np
import pandas as pd
import datetime as dt
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.transactions as trans
import oandapyV20.endpoints.pricing as pricing

#%
class Translator(object):
    """

    """

    def __init__(self):
        # self.broker = broker
        # self.accountID = accountID
        # self.token = token
        # if broker == 'oanda':
        #     self.client = oandapyV20.API(access_token=token)
        pass

    def open(self, broker, accountID, token, type, pair, price, vol, slip):
        # Fill or Kill (?)
        if broker == "oanda":
            client = oandapyV20.API(access_token=token)
            if type == 'l':
                priceB = (1 + slip) * price
            if type == 's':
                priceB = (1 - slip) * price
            data = \
                {
                    "order": {
                        "units": str(vol),
                        "instrument": pair,
                        "timeInForce": "FOK",
                        "type": "MARKET",
                        "positionFill": "OPEN_ONLY",
                        "priceBound": str(priceB)
                    }
                }
            r = orders.OrderCreate(accountID, data = data)
            client.request(r)
            # reply = dict(r.response)
            # if "orderFillTransaction" in reply.keys():
            #     OFT = reply["orderFillTransaction"]
            #     print(OFT)
            #     posID = OFT["tradeOpened"]["tradeID"]
            #     iprice = float(OFT["price"])
            #     ivol = float(OFT["units"])
            #     t = pd.Timestamp(OFT["time"], tzinfo = 'UTC')
            #     pos = Position(broker, posID, pair, iprice, ivol, type, t)
            #     pos.status = 'o'
            #     return(pos)
            # else:
            #     return(None)

    def close(self, broker, accountID, token, pos, vol): # also price
        if vol <= pos.log.iloc[-1,].at['vol']:
            if pos.broker == "oanda":
                client = oandapyV20.API(access_token=token)
                # if pos.status == 'w':
                #     r = orders.OrderCancel(accountID = self.accountID, orderID = posID)
                #     client.request(r)
                #     reply = dict(r.response)
                #     v = pos.orderLog.iloc[-1, 'volLeft']
                #     p = pos.orderLog.iloc[-1, 'price']
                #     t = pd.to_datetime(reply["orderCancelTransaction"]["time"])
                #     pos.orderLog.loc[t] = pd.DataFrame({'volLeft': v, 'price': p})
                data = \
                {
                    "units": str(vol)
                }
                r = trades.TradeClose(accountID = accountID, tradeID = pos.posID, data = data)
                client.request(r)
                # reply = dict(r.response)
                # OFT = reply["orderFillTransaction"]
                # print(OFT)
                # v = pos.log.iloc[-1,].at['vol'] + float(OFT["units"])
                # p = float(OFT["price"])
                # cp = pos.log.iloc[-1,].at['closedprof'] + float(OFT["pl"])
                # t = pd.Timestamp(pd.Timestamp(OFT["time"]))
                # pos.log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp}
                # pos.status = 'c'
                # return(r.response)

    def initPosLog(self, broker, accountID, token, pairList = [], posList = []):
        if broker == "oanda":
            client = oandapyV20.API(access_token = token)
            r = trades.OpenTrades(accountID = accountID)
            client.request(r)
            reply = dict(r.response)
            tList = reply["trades"]
            tList.reverse()
            for T in tList:
                ro = trades.TradeDetails(accountID = accountID, tradeID=T["id"])
                client.request(ro)
                reply = dict(ro.response)
                oT = reply["trade"]
                if not oT["instrument"] in cfg.pairList:
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
        return(pairList, posList)

    def updatePosLog(self, pairList, posList, broker, accountID):
        oT = dict(cfg.brokerList["oanda"]["account"]["tsv"].__next__())
        print(json.dumps(oT, indent=4))
        if oT["type"] == "ORDER_FILL":
            if "tradeOpened" in oT.keys():
                oC = oT["tradeOpened"]
                tempL = [o for o in posList if o.posID == oC["id"]]
                if tempL == []:
                    if not oT["instrument"] in cfg.pairList:
                        pairList.append(oC["instrument"])
                        pairList.sort()
                    print(oC)
                    if float(oC["initialUnits"]) >= 0:
                        typePos = 'l'
                    else:
                        typePos = 's'
                    posList.append(td.Position('oanda', accountID, oC["id"], oC["instrument"], float(oC["price"]), abs(float(oC["initialUnits"])), typePos, pd.Timestamp(oC["openTime"])))
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
#%%
class Position(object):
    """

    """

    # transl = Translator()
    
    def __init__(self, broker, account, posID, pair, initPrice, initVol, typePos, t, stopLoss = 0, takeProfit = 100000): # Dictionary for pairs missing
        self.broker = broker
        self.account = account
        self.posID = posID
        self.status = 'w' #w: waiting, o: open, c:close
        self.pair = pair
        self.initPrice = initPrice #open price
        self.initVol = initVol #initial position volume
        self.log = pd.DataFrame({'vol': [initVol], 'price': [initPrice], 'closedprof': [float(0)]}, index = [t])
        self.orderLog = pd.DataFrame({'volLeft': [initVol], 'price': [initPrice]}, index = [t])
        self.tradeVol = 0
        self.typePos = typePos #l: long, s: short
        self.profit = 0 #result of position at instant t
        self.cost = 0
        # self.t = t #last ticket
        # self.entry = entryPos #price to enter position
        # self.exit = exitPos #price to exit position
        self.stopLoss = stopLoss #hard coded stop loss broker side
        self.takeProfit = takeProfit #hard coded take profit broker side
        # self.log = pd.Series([np.NaN, np.NaN],index = ['entry', 'exit'])


    def profitcalc(self, price):
        if self.typePos == 'l':
            return(self.log.closedprof[-1] + self.tradeVol * price - self.cost)
        if self.typePos == 's':
            return(self.log.closedprof[-1] + self.cost - self.tradeVol * price)

    def tick(self, t, price):
#        if self.status == 'o':
#            self.log.append([t, price])
        self.profit = self.profitcalc(price)
        return([t, price, self.profit])

        
    # def closePos(self, vol):
    #     self.transl.close(self.broker, self.account, cfg.brokerList[self.broker]["token"], self, vol)

#% Temp
