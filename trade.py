import pandas as pd
import numpy as np
#%%
class position(object):
    """
    
    """
    
    def __init__(self, pair, size = 0, typePos, t, entryPos = 0, exitPos = 0):
        self.status = 'w'
        self.pair = pair
        self.initPrice = 0
        self.size = size
        self.typePos = typePos
        self.profit = 0
        self.t = t
        self.entry = entryPos
        self.exit = exitPos
        self.log = pd.Series([np.NaN, np.NaN],index = ['entry', 'exit'])
        
    def profit(self, price):
        if self.typePos == 'l':
            return(size * (price - self.initPrice))
        if self.typePos == 's':
            return(size * (self.initPrice - price))
    
    def tick(self,t, price):
#        if self.status == 'o':
#            self.log.append([t, price])
        return([t, price, self.profit])
        
    def openPos(self, t, price):
        self.initPrice = price
        self.log.append([t, price])
        self.profit = price - self.initPrice
        
    def closePos(self, t, price):
        if time != self.log[-1][0]:
            self.log.append([t, price])
            self.profit = price - self.initPrice
        self.status = 'c'