import numpy as np
import pandas as pd
import datetime as dt

#%%
class Position(object):
    """

    """
    
    def __init__(self, broker, posID, pair, initPrice, initVol, typePos, t, stopLoss, takeProfit):
        self.broker = broker
        self.posID = posID
        self.status = 'o' #w: waiting, o: open, c:close
        self.pair = pair
        self.initPrice = initPrice #open price
        self.initVol = initVol #initial position volume
        self.log = pd.DataFrame({vol: 0}, {price: initPrice}, {closedprof: 0}, index = t)
        self.orderLog = pd.DataFrame({volLeft: 0}, {price: initPrice}, index = t)
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
            return(self.closedVol.closedprof[-1] + self.tradeVol * price - self.cost)
        if self.typePos == 's':
            return(self.closedVol.closedprof[-1] + self.cost - self.tradeVol * price)
    
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
        if vol <= self.tradeVol:
            self.orderlog.loc[t] = {'vol': vol, 'price': price, 'clo}
            self.profit = price - self.initPrice
        self.status = 'c'

class PosOanda(Position):
    """
    
    """

    def __init__(self, pair, size, typePos, t, entryPos, exitPos, stopLoss, takeProfit):
        self.status = 'w' #w: waiting, o: open, c:close
        self.pair = pair
        self.initPrice = 0 #open price
        self.size = size
        self.typePos = typePos #l: long, s: short
        self.profit = 0 #result of position at instant t
        self.t = t #last ticket
        self.entry = entryPos #price to enter position
        self.exit = exitPos #price to exit position
        self.stopLoss=stopLoss #hard coded stop loss broker side
        self.takeProfit=takeProfit #hard coded take profit broker side
        self.log = pd.Series([np.NaN, np.NaN],index = ['entry', 'exit'])