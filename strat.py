import datetime as dt
import pandas as pd
import numpy as np

#%%
class Strategy(object):
    """
    
    """
    
    def indicator_adv(self, pos, time):
        pass
    
    def advice(self, pos, time):
        if pos.status == 'o':
            return self.indicator_adv(pos, time)

#%%
#%%
IKH = strategy()

def ind(time, log, period = 86400):
    postenkansen = argmin(time - 26 * period)
    if

