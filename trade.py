import pandas as pd
import numpy as np
#%%
class position(object):
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
        
    def profit(self, price):
        if self.typePos == 'l':
            return(self.size * (price - self.initPrice))
        if self.typePos == 's':
            return(self.size * (self.initPrice - price))
    
    def tick(self, t, price):
#        if self.status == 'o':
#            self.log.append([t, price])
        return([t, price, self.profit])
        
    def openPos(self, t, price, typePos):
        self.initPrice = price
        self.log.append([t, price])
        self.typePos=typePos
        self.profit = price - self.initPrice
        
    def closePos(self, t, price):
        if self.time != self.log[-1][0]:
            self.log.append([t, price])
            self.profit = price - self.initPrice
        self.status = 'c'
