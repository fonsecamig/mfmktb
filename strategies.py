import numpy as np
import pandas as pd

import config as cfg

class TestStrategy(object):
    """

    """

    def __init__(self, volTest, slip, perProfit, perLoss):
        self.volTest = volTest
        self.slip = slip
        self.perProfit = perProfit
        self.perLoss = perLoss

    def advice(self, posList):
        orders = []
        for broker in cfg.brokerList:
            for acc in cfg.brokerList[broker]["accounts"]:
                for pair in cfg.pairList:
                    pList = [pos for pos in cfg.posList if pos.broker == broker and pos.account == acc and pos.pair == pair]
                    if pList == []:
                        orders.append({'oType': 'o', 'broker': broker, 'account': acc, 'type': 'l', 'pair': pair, 'vol': self.volTest,
                                       'price': cfg.priceList[broker][acc].loc[pair], 'slip': self.slip})
                    else:
                        profitLPer = pd.Series([p.profitcalc(cfg.priceList[broker][acc].loc[pair] / (p.initPrice * p.initVol)) for p in pList])
                        if profitLPer.max() > self.perProfit:
                            orders.append(
                                {'oType': 'o', 'broker': broker, 'account': acc, 'type': pList[-1].type, 'pair': pair, 'vol': self.volTest,
                                 'price': cfg.priceList[broker][acc].loc[pair], 'slip': self.slip})
                        if profitLPer.sum < (pList.__len__() - 1) * self.perProfit * self.perLoss:
                            for pos in pList:
                                orders.append(
                                    {'oType': 'o', 'broker': broker, 'account': acc, 'pos': pos, 'vol': self.volTest})
