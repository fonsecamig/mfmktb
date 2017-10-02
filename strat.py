import datetime as dt
import numpy as np

#%%
class strategy(object):
    """
    
    """
    
    def indicatorAdv(self, pos, time):
        pass
    
    def advice(self, pos, time):
        if pos.status == 'o':
            return(self.indicatorAdv(pos, time))
        

#%%
IKH = strategy()

def ind(time, log):
    daybef = dt.utcfromtimestamp(dt.datetime.utcfromtimestamp(time) - dt.timedelta(seconds = time))
    np.searchsorted(daybef)