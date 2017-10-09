import datetime as dt
import pandas as pd
import numpy as np

#%%
class Strategy:
    """
    
    """

    def __init__(self, params = {})
        self.params = params

    def indicator_adv(self, pos, time):
        pass
    
    def advice(self, pos, time):
        if pos.status == 'o':
            return self.indicator_adv(pos, time)

#%%

#%%
class IKH(Strategy):
    """
    Ichimoku Kinko Hyo based class
    """

    def __init__(self, period = 86400, pts = 26, pks = 8, pssb = 52, pahead = 22):
        self.period = period
        self.pts = pts
        self.pks = pks
        self.pssb = pssb
        self.pahead = pahead

    def IKS(self, timet, logprice):
        if np.argmin(timet - (self.pssb + self.pahead) * self.period) == 0:
            res = np.NaN
        else:
            pos_tenkansen = np.argmin(timet - self.pts * self.period)  # Tenkan Sen position
            pos_kijunsen = np.argmin(timet - self.pks * self.period)  # Kijun Sen position
            pos_senkouspan_b = np.argmin(timet - (self.pssb + self.pahead) * self.period)  # Kijun Sen position
            kansen = (max(logprice[pos_tenkansen:-1]) + min(logprice[pos_tenkansen:-1])) / 2
            kinjun = (max(logprice[pos_kijunsen:-1]) + min(logprice[pos_kijunsen:-1])) / 2
            senkouspan_a = (max(logprice[(pos_tenkansen - self.pahead):(-1 - self.pahead)]) + min(logprice[(pos_tenkansen - self.pahead):(-1 - self.pahead)]) + max(logprice[(pos_kijunsen - self.pahead):(-1 - self.pahead)]) + min(logprice[(pos_kijunsen - self.pahead):(-1 - self.pahead)])) / 4
            senkouspan_b = (max(logprice[pos_senkouspan_b:-self.pts]) + min(logprice[pos_senkouspan_b:-self.pts])) / 2
            chikouspan = logprice[timet - self.pahead]
            res = {kansen: kansen, kinjun: kinjun, senkouspan_a: senkouspan_a, senkouspan_b: senkouspan_b,
                   chikouspan}
        return res

    def indicator_adv(self, pos, timet):
        ind = self.IKS(timet)
        if pos.status = 'o':
           if pos.type = 'l':
               if price < ind[kansen] & ind[chikouspan]:
                   if max(ind[senkouspan_a, senkouspan_b]) < price:
                       pos