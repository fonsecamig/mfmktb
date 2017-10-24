import numpy as np
import pandas as pd
import datetime as dt
import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import numpy as np
import pandas as pd

#%
class Translator(object):
    """

    """

    def __init__(self, broker, accountID, token):
        self.broker = broker
        self.accountID = accountID
        self.token = token
        if broker == 'oanda':
            self.client = oandapyV20.API(access_token=token)

    def open(self, type, pair, price, vol, slip):
        # Fill or Kill (?)
        if self.broker == "oanda":
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
            r = orders.OrderCreate(self.accountID, data = data)
            self.client.request(r)
            reply = dict(r.response)
            print(reply)
            if "orderFillTransaction" in reply.keys():
                OFT = reply["orderFillTransaction"]
                print(OFT)
                posID = OFT["tradeOpened"]["tradeID"]
                iprice = float(OFT["price"])
                ivol = float(OFT["tradeOpened"]["units"])
                t =
                pos = Position(self.broker, posID, pair, iprice, ivol, type, t)
                return(pos)
            else:
                return(None)

    def close(self, pos, vol):
        if pos.broker == "oanda":
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
            r = trades.TradeClose(accountID = self.accountID, data = data)
            self.client.request(r)
            reply = dict(r.response)
            v = pos.log.iloc[-1,].at['vol'] - float(reply["OrderFillTransaction"]["units"])
            p = float(reply["OrderFillTransaction"]["price"])
            cp = pos.log.iloc[-1,].at['closedprofit'] + reply["OrderFillTransaction"]["pl"]
            t = pd.Timestamp(pd.to_datetime(reply["OrderFillTransaction"]["time"]))
            pos.log.loc[t] = pd.DataFrame({'vol': [v], 'price': [p], 'closedprofit': [cp]})
            return(r.response)

#%%
class Position(object):
    """

    """
    
    def __init__(self, broker, posID, pair, initPrice, initVol, typePos, t, stopLoss = 0, takeProfit = 100000): # Dictionary for pairs missing
        self.broker = broker
        self.posID = posID
        self.status = 'w' #w: waiting, o: open, c:close
        self.pair = pair
        self.initPrice = initPrice #open price
        self.initVol = initVol #initial position volume
        self.log = pd.DataFrame({'vol': [0], 'price': [initPrice], 'closedprof': [0]}, index = [t])
        self.orderLog = pd.DataFrame({'volLeft': [initVol], 'price': [initPrice]}, index = [t])
        self.tradeVol = 0
        self.typePos = typePos #l: long, s: short
        self.profit = 0 #result of position at instant t
        self.cost = 0
        # self.t = t #last ticket
        # self.entry = entryPos #price to enter position
        # self.exit = exitPos #price to exit position
        self.stopLoss=stopLoss #hard coded stop loss broker side
        self.takeProfit=takeProfit #hard coded take profit broker side
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
        
    # def openPos(self, t, price, typePos):
    #     self.initPrice = price
    #     self.log.append([t, price])
    #     self.typePos=typePos
    #     self.profit = price - self.initPrice
        
    def closePos(self, t, vol, price):
        self.trans.close(self, vol)
        # if self.status == 'o':
        #     if vol <= self.tradeVol:
        #         self.orderlog.loc[t] = {'vol': vol, 'price': price, 'clo': }
        #         self.profit = price - self.initPrice
        #     self.status = 'c'

#% Temp
