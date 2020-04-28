import numpy as np
import pandas as pd
import config as cfg


class Strategy3Pairs(object):
    """

    """

    def __init__(self, broker_name, account_idx, pairs,
                 vol_init, slip, profit_per_pair, loss_per_pair, profit_global, loss_global):
        self.pairs = pairs
        self.broker_name = broker_name
        self.account_idx = account_idx
        self.volTest = vol_init
        self.slip = slip
        self.perProfit = profit_per_pair
        self.perLoss = loss_per_pair
        self.profit_global = profit_global
        self.loss_global = loss_global

    def initiate(self):
        pass  # todo: check for already positions

    def advice(self):
        orders = []
        for broker in self.broker_name:
            for acc in self.account_idx:
                for pair in cfg.pairList:
                    pList = [cfg.posList.index(pos) for pos in cfg.posList if
                             pos.broker == broker and pos.account == acc and pos.pair == pair and pos.status == 'o']
                    print(pList)
                    if pList == []:
                        orders.append({'oType': 'o', 'broker': broker, 'account': acc, 'type': 'l', 'pair': pair,
                                       'vol': self.volTest,
                                       'price': cfg.priceList[broker]['accounts'][acc].loc[pair]['ask'],
                                       'slip': self.slip})
                    elif pList.__len__() == 1:
                        if cfg.posList[pList[0]].tick() / (
                                cfg.posList[pList[0]].initPrice * cfg.posList[pList[0]].initVol) - 1 < -self.perProfit:
                            orders.append(
                                {'oType': 'c', 'broker': broker, 'account': acc, 'pos': pList[0], 'vol': self.volTest})
                            if cfg.posList[pList[0]].typePos == 'l':
                                tPos = 's'
                            else:
                                tPos = 'l'
                            orders.append({'oType': 'o', 'broker': broker, 'account': acc, 'type': tPos, 'pair': pair,
                                           'vol': self.volTest,
                                           'price': cfg.priceList[broker]['accounts'][acc].loc[pair]['ask'],
                                           'slip': self.slip})
                    else:
                        profitLPer = pd.Series(
                            [cfg.posList[p].tick() / (cfg.posList[p].initPrice * cfg.posList[p].initVol) - 1 for p in
                             pList])
                        print(profitLPer)
                        if profitLPer.max() > self.perProfit:
                            if cfg.posList[pList[-1]] == 'l':
                                priceT = 'ask'
                            else:
                                priceT = 'bid'

                            orders.append(
                                {'oType': 'o', 'broker': broker, 'account': acc, 'type': pList[-1].typePos,
                                 'pair': pair, 'vol': self.volTest,
                                 'price': cfg.priceList[broker][acc].loc[pair][priceT], 'slip': self.slip})
                        elif profitLPer.sum() < max([pList.__len__() - 1, 1]) * self.perProfit * self.perLoss:
                            for pos in pList:
                                orders.append(
                                    {'oType': 'c', 'broker': broker, 'account': acc, 'pos': pos, 'vol': self.volTest})
                        # print([(p.status, p.log) for p in pList])
        return (orders)
