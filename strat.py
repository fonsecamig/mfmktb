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
def IKS(timet, logprice, period = 86400, pts = 8, pks = 22, pssb = 52, pahead = 26):
    if np.argmin(timet - (pssb + pahead) * period) == 0:
        res = np.NaN
    else:
        pos_tenkansen = np.argmin(timet - pts * period)  # Tenkan Sen position
        pos_kijunsen = np.argmin(timet - pks * period)  # Kijun Sen position
        pos_senkouspan_b = np.argmin(timet - (pssb + pahead) * period)  # Kijun Sen position
        kansen = (max(logprice[pos_tenkansen:-1]) + min(logprice[pos_tenkansen:-1])) / 2
        kinjun = (max(logprice[pos_kijunsen:-1]) + min(logprice[pos_kijunsen:-1])) / 2
        senkouspan_a = (max(logprice[(pos_tenkansen - pahead):(-1 - pahead)]) + min(logprice[(pos_tenkansen - pahead):(-1 - pahead)]) + max(logprice[(pos_kijunsen - pahead):(-1 - pahead)]) + min(logprice[(pos_kijunsen - pahead):(-1 - pahead)])) / 4
        senkouspan_b = (max(logprice[pos_senkouspan_b:-26]) + min(logprice[pos_senkouspan_b:-26])) / 2
        chikouspan =  logprice[timet - pahead]
        res ={kansen: kansen, kinjun: kinjun, senkouspan_a: senkouspan_a, senkouspan_b: senkouspan_b, chikouspan}
    return res

#%%
class IKH(Strategy):
    """

    """

    def __init__(self)
        self.params = {period = 86400, pts: pts, pks: pks, pssb: pssb, pahead: pahead}

    def indicator_adv(pos, time):
        if pos.status = 'o':
            if pos.type = 'l':

