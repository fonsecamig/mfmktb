import numpy as np
import pandas as pd

import trade as td
import config as cfg

transl0 = td.Translator()

class Gasoline(object):
    """

    """

    def __init__(self, vol, slip, perProfit, perLoss, mult):
        self.vol = vol
        self.slip = slip
        self.perProfit = perProfit
        self.perLoss = perLoss
        self.mult = mult
        self.refL = {}
        self.lastType = {}

    def lossF(self, x):
        return(np.log10(x))

    def initiate(self):
        for broker in cfg.brokerList:
            self.refL[broker] = {}
            self.lastType[broker] = {}
            for acc in range(cfg.brokerList[broker]["accounts"].__len__()):
                self.refL[broker][acc] = {}
                self.lastType[broker][acc] = {}
                for pair in cfg.pairList:
                    pList = [cfg.posList.index(pos) for pos in cfg.posList if
                             pos.broker == broker and pos.account == acc and pos.pair == pair and pos.status == 'o']
                    if pList == []:
                        self.lastType[broker][acc][pair] = np.random.choice(['l', 's'])
                    else:
                        minT = pd.Series([cfg.posList[pos].log.index[0] for pos in pList]).min()
                        # profitL = pd.Series([cfg.posList[pList[p]].tick() for p in pList])
                        # volL = pd.Series([cfg.posList[pList[p]].initVol for p in pList])
                        # profitPerPos = profitL.sum / volL.sum
                        if cfg.posList[pList[0]].typePos == 'l':
                            self.refL[broker][acc][pair] = transl0.histPrice(broker, acc, pair, minT).h
                            self.lastType[broker][acc][pair] = 's'
                        if cfg.posList[pList[0]].typePos == 's':
                            self.refL[broker][acc][pair] = transl0.histPrice(broker, acc, pair, minT).l
                            self.lastType[broker][acc][pair] = 'l'
        print(self.lastType)
        print(self.refL)

    def lossF(self, p):
        return(np.log10(p))

    def advice(self):
        orders = []
        print(self.lastType)
        for broker in cfg.brokerList:
            for acc in range(cfg.brokerList[broker]["accounts"].__len__()):
                for pair in cfg.pairList:
                    pList = [cfg.posList.index(pos) for pos in cfg.posList if
                             pos.broker == broker and pos.account == acc and pos.pair == pair and pos.status == 'o']
                    if pList == []:
                        if self.lastType[broker][acc][pair] == 'l':
                            newType = 's'
                        if self.lastType[broker][acc][pair] == 's':
                            newType = 'l'
                        orders.append({'oType': 'o', 'broker': broker, 'account': acc, 'type': newType, 'pair': pair, 'vol': self.vol, 'price': cfg.priceList[broker]['accounts'][acc].loc[pair]['ask'], 'slip': self.slip})
                    else:
                        profitL = pd.Series([cfg.posList[p].tick() for p in pList])
                        volL = pd.Series([cfg.posList[p].initVol for p in pList])
                        profitPerPos = profitL.sum() / volL.sum()
                        if cfg.posList[pList[-1]] == 'l':
                            if cfg.priceList[broker]['accounts'][acc].bid[pair] < (1 - self.perLoss) * cfg.posList[pList[-1]].initPrice:
                                orders.append({'oType': 'o', 'broker': broker, 'account': acc,
                                               'type': cfg.posList[pList[0]].typePos, 'pair': pair,
                                               'vol': self.mult * cfg.posList[pList[0]].initVol,
                                               'price': cfg.priceList[broker]['accounts'][acc].loc[pair].ask, 'slip': self.slip})
                            else:
                                if profitPerPos > self.perProfit:
                                    self.refL[broker][acc][pair] = cfg.priceList[broker]['accounts'][acc].loc[pair].bid
                                    orders.append({'oType': 'o', 'broker': broker, 'account': acc,
                                                   'type': cfg.posList[pList[0]].typePos, 'pair': pair,
                                                   'vol': self.mult * cfg.posList[pList[0]].initVol,
                                                   'price': cfg.priceList[broker]['accounts'][acc].loc[pair].ask,
                                                   'slip': self.slip})
                                else:
                                    profitH = pd.Series([cfg.posList[pList[p]].pl(self.refL[broker][acc][pair]) for p in pList])
                                    profitPerPosH = profitH.sum / volL.sum
                                    if profitPerPos < self.lossF(profitPerPosH) and self.refL[broker][acc][pair] > cfg.priceList[broker]['accounts'][acc].loc[pair].bid:
                                        for pos in pList:
                                            orders.append({'oType': 'c', 'broker': broker, 'account': acc, 'pos': pos, 'vol': cfg.posList[pList[pos]].log.vol[-1]})
                                            self.lastType[broker][acc][pair] = 'l'
                        if cfg.posList[pList[-1]] == 's':
                            if cfg.priceList[broker]['accounts'][acc].bid[pair] < (1 - self.perLoss) * cfg.posList[pList[-1]].initPrice:
                                orders.append({'oType': 'o', 'broker': broker, 'account': acc,
                                               'type': cfg.posList[pList[0]].typePos, 'pair': pair,
                                               'vol': self.mult * cfg.posList[pList[0]].initVol,
                                               'price': cfg.priceList[broker]['accounts'][acc].loc[pair]['bid'], 'slip': self.slip})
                            else:
                                if profitPerPos > self.perProfit:
                                    self.refL[broker][acc][pair] = cfg.priceList[broker][acc].loc[pair].ask
                                    orders.append({'oType': 'o', 'broker': broker, 'account': acc,
                                                   'type': cfg.posList[pList[0]].typePos, 'pair': pair,
                                                   'vol': self.mult * cfg.posList[pList[0]].initVol,
                                                   'price': cfg.priceList[broker]['accounts'][acc].loc[pair]['bid'],
                                                   'slip': self.slip})
                                else:
                                    profitH = pd.Series([cfg.posList[p].pl(self.refL[broker][acc][pair]) for p in pList])
                                    profitPerPosH = profitH.sum() / volL.sum()
                                    if profitPerPos < self.lossF(profitPerPosH) and self.refL[broker][acc][pair] > cfg.priceList[broker]['accounts'][acc].loc[pair].ask:
                                        for pos in pList:
                                            orders.append({'oType': 'c', 'broker': broker, 'account': acc, 'pos': pos, 'vol': cfg.posList[pos].log.vol[-1]})
                                            self.lastType[broker][acc][pair] = 's'
                        # if cfg.posList[pList[-1]] == 'l':
                        #     priceT = 'ask'
                        # else:
                        #     priceT = 'bid'
                        # if profitLPer.max() > self.perProfit:
                        #     orders.append(
                        #         {'oType': 'o', 'broker': broker, 'account': acc, 'type': pList[-1].typePos,
                        #          'pair': pair, 'vol': self.volTest,
                        #          'price': cfg.priceList[broker][acc].loc[pair][priceT], 'slip': self.slip})
                        # elif profitLPer.sum() < max([pList.__len__() - 1, 1]) * self.perProfit * self.perLoss:
                        #     for pos in pList:
                        #         orders.append(
                        #             {'oType': 'c', 'broker': broker, 'account': acc, 'pos': pos, 'vol': cfg.posList[pList[pos]].log.vol[-1]})
                        #         # print([(p.status, p.log) for p in pList])
        return(orders)