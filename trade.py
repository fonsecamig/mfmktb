import os
import copy
import numpy as np
import pandas as pd
import json
import csv
import oandapyV20
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.transactions as trans
import oandapyV20.endpoints.pricing as pricing
from oandapyV20.contrib.factories import InstrumentsCandlesFactory

import config as cfg


def nDays(self, y, m):
    if m in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif m != 2:
        return 30
    else:
        if y % 4 != 0:
            return 28
        else:
            return 29


# %
class Translator(object):
    """

    """

    def __init__(self):
        pass

    def initAccount(self, broker, token, iYear=2018, iMonth=1, fYear=2018, fMonth=3, btpath='./', btcurr='USD',
                    btamount=100000,
                    btmargin=0.02):
        if broker == 'backtest':  # Introduce pairs in config.py
            cfg.brokerList['backtest'] = {'path': btpath,
                                          'iYear': iYear,
                                          'iMonth': iMonth,
                                          'fYear': fYear,
                                          'fMonth': fMonth,
                                          # 'gran': gran,
                                          'accounts': []}
            cfg.brokerList['backtest']['accounts'] = [{'ID': 0,
                                                       'filelist': dict(
                                                           zip(cfg.pairList, cfg.pairList.__len__() * [[]])),
                                                       'fileiter': dict(
                                                           zip(cfg.pairList, cfg.pairList.__len__() * [[]])),
                                                       'tickTable': None,
                                                       'tickIter': None,
                                                       'histTable': None,
                                                       'histBuffer': None,
                                                       'margin': btmargin,
                                                       'curr': btcurr,
                                                       'initAmount': btamount,
                                                       'log': pd.DataFrame({'balance': [], 'NAV': []}, index=[])}]
            cfg.priceList['backtest'] = {'accounts': [pd.DataFrame(
                {'ask': cfg.pairList.__len__() * [None], 'bid': cfg.pairList.__len__() * [None],
                 'ts': cfg.pairList.__len__() * [None]}, index=cfg.pairList)]}
            for pair in cfg.pairList:
                lst = []
                for year in range(cfg.brokerList['backtest']['iYear'], cfg.brokerList['backtest']['fYear'] + 1):
                    yStr = str(year)
                    initM = 1
                    finalM = 12
                    if year == cfg.brokerList['backtest']['iYear']:
                        initM = cfg.brokerList['backtest']['iMonth']
                    if year == cfg.brokerList['backtest']['fYear']:
                        finalM = cfg.brokerList['backtest']['fMonth']
                    rngMonth = range(initM, finalM + 1)
                    for month in rngMonth:
                        if month < 10:
                            mString = '0' + str(month)
                        else:
                            mString = str(month)
                        st = str('-'.join([cfg.dctPredInv[pair], yStr, mString]) + '.csv')
                        lst.append(str(st))
                cfg.brokerList['backtest']['accounts'][0]['filelist'][pair] = lst
                cfg.brokerList['backtest']['accounts'][0]['fileiter'][pair] = iter(lst)

        if broker == 'oanda':
            client = oandapyV20.API(access_token=token)
            r = accounts.AccountList()
            rv = dict(client.request(r))
            cfg.brokerList['oanda'] = {'token': token}
            cfg.brokerList['oanda']['accounts'] = []
            cfg.priceList['oanda'] = {}
            cfg.priceList['oanda']['accounts'] = []
            for acc in rv["accounts"]:
                ra = accounts.AccountDetails(acc["id"])
                rav = dict(client.request(ra))
                cfg.brokerList['oanda']['accounts'].append(
                    {'ID': acc["id"], 'tsv': None, 'psv': None,
                     'margin': float(rav["account"]["marginRate"]),
                     'curr': rav["account"]["currency"], 'log': pd.DataFrame(
                        {'bal': [float(rav["account"]["balance"])], 'NAV': [float(rav["account"]["NAV"])],
                         'mused': [float(rav["account"]["marginUsed"])]}, index=[pd.Timestamp.now(tz='utc')])})
                cfg.priceList['oanda']['accounts'].append(None)

    def open(self, broker, accountID, typeP, pair, vol, price, slip):  # Falta log
        try:
            if broker == "backtest":
                cfg.posList.append(Position('backtest', accountID, str(accountID), pair, price, vol, typeP,
                                            cfg.priceList['backtest']['accounts'][accountID].ts.max()))
                cfg.posList[-1].status = 'o'
                if pair[-3:] == cfg.brokerList[broker]['accounts'][accountID]['curr']:
                    conv = 1
                elif ('_').join([pair[-3:], cfg.brokerList[broker]['accounts'][accountID]['curr']]) in \
                        cfg.priceList[broker]['accounts'][accountID].index:
                    conv = cfg.priceList[broker]['accounts'][accountID].bid[
                        ('_').join([pair[-3:], cfg.brokerList[broker]['accounts'][accountID]['curr']])]
                elif ('_').join([cfg.brokerList[broker]['accounts'][accountID]['curr'], pair[-3:]]) in \
                        cfg.priceList[broker]['accounts'][accountID].index:
                    conv = cfg.priceList[broker]['accounts'][accountID].ask[('_').join(
                        [cfg.brokerList[broker]['accounts'][accountID]['curr'], pair[-3:]])] ** (-1)
                bal = cfg.brokerList['backtest']['accounts'][accountID]['log'].iloc[-1,].balance - price * vol * conv
                nav = bal + pd.Series([po.tick() for po in cfg.posList if po.status == 'o']).sum()
                cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[
                    cfg.priceList['backtest']['accounts'][accountID].ts.max()] = {'balance': bal, 'NAV': nav}
            if broker == "oanda":
                client = oandapyV20.API(access_token=cfg.brokerList['oanda']['token'])
                if typeP == 'l':
                    sign = 1
                    priceB = (1 + slip) * price
                if typeP == 's':
                    sign = -1
                    priceB = (1 - slip) * price
                data = \
                    {
                        "order": {
                            "units": str(sign * vol),
                            "instrument": pair,
                            "timeInForce": "FOK",
                            "type": "MARKET",
                            "positionFill": "OPEN_ONLY",
                            "priceBound": str(round(priceB, 5))
                        }
                    }
                r = orders.OrderCreate(cfg.brokerList['oanda']['accounts'][accountID]['ID'], data=data)
                ro = dict(client.request(r))
                if "orderFillTransaction" in ro.keys():
                    oT = ro["orderFillTransaction"]
                    if "tradeOpened" in oT.keys():
                        oC = oT["tradeOpened"]
                        tempL = [o for o in cfg.posList if o.posID == oC["tradeID"]]
                        if tempL == []:
                            if not oT["instrument"] in cfg.pairList:
                                cfg.pairList.append(oT["instrument"])
                                cfg.pairList.sort()
                                client = oandapyV20.API(access_token=cfg.brokerList['oanda']['token'])
                                parstreamtrans = \
                                    {
                                        "instruments": ",".join(cfg.pairList)
                                    }
                                pstream = pricing.PricingStream(
                                    accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'],
                                    params=parstreamtrans)
                                cfg.brokerList[broker]['psv'] = client.request(pstream)
                            if float(oC["units"]) >= 0:
                                typePos = 'l'
                            else:
                                typePos = 's'
                            cfg.posList.append(
                                Position('oanda', accountID, oC["tradeID"], oT["instrument"], float(oT["price"]),
                                         abs(float(oC["units"])), typePos, pd.Timestamp(oT["time"])))
                            cfg.posList[-1].status = 'o'
                            cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[pd.Timestamp(oT["time"])] = float(
                                oT["accountBalance"])
        finally:
            pass

    def close(self, broker, accountID, pos, vol):
        try:
            if vol <= cfg.posList[pos].log.iloc[-1,].at['vol']:
                if cfg.posList[pos].broker == "backtest":
                    if cfg.priceList['backtest']['accounts'][accountID].loc[cfg.posList[pos].pair].ts > \
                            cfg.posList[pos].log.index[-1]:
                        if cfg.posList[pos].typePos == 'l':
                            tTrans = 'bid'
                        if cfg.posList[pos].typePos == 's':
                            tTrans = 'ask'
                        v = cfg.posList[pos].log.iloc[-1,].vol - vol
                        p = cfg.priceList['backtest']['accounts'][accountID].loc[cfg.posList[pos].pair][tTrans]
                        cp = cfg.posList[pos].log.iloc[-1,].closedprof + cfg.posList[pos].pl(p)
                        comm = 0
                        t = cfg.priceList['backtest']['accounts'][accountID].ts.max()
                        print(v, p, cp, t)
                        cfg.posList[pos].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp, 'commission': comm}
                        if cfg.posList[pos].log.loc[t].vol == 0:
                            cfg.posList[pos].status = 'c'
                        # cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[t] = {'balance': cfg.brokerList['backtest']['accounts'][accountID]['log'].iloc[-1,].balance + cp, 'NAV': None}
                        bal = cfg.brokerList['backtest']['accounts'][accountID]['log'].iloc[-1,].balance + cfg.posList[
                            pos].tick()
                        nav = bal + pd.Series(
                            [po.tick() for po in cfg.posList if po.status == 'o']).sum()
                        cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[
                            cfg.priceList['backtest']['accounts'][accountID].ts.max()] = {'balance': bal, 'NAV': nav}
                if cfg.posList[pos].broker == "oanda":
                    client = oandapyV20.API(access_token=cfg.brokerList['oanda']['token'])
                    data = \
                        {
                            "units": str(vol)
                        }
                    r = trades.TradeClose(accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'],
                                          tradeID=cfg.posList[pos].posID, data=data)
                    ro = dict(client.request(r))
                    print(json.dumps(ro, indent=4))
                    if "orderFillTransaction" in ro.keys():
                        oT = ro["orderFillTransaction"]
                        if "tradesClosed" in oT.keys():
                            oCl = oT["tradesClosed"]
                            oCl.reverse()
                            for ocp in oCl:
                                iL = [j for j in range(cfg.posList.__len__()) if
                                      cfg.posList[j].account == accountID and cfg.posList[j].posID == ocp["tradeID"]]
                                i = int(iL[0])
                                v = cfg.posList[i].log.iloc[-1,].vol - abs(float(ocp["units"]))
                                p = oT["price"]
                                cp = float(ocp["realizedPL"])
                                comm = float(oT["commission"])
                                t = pd.Timestamp(oT["time"])
                                cfg.posList[i].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp, 'commission': comm}
                                if cfg.posList[i].log.loc[t].vol == 0:
                                    cfg.posList[i].status = 'c'
                                cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[t] = float(
                                    oT["accountBalance"])
                        if "tradeReduced" in oT.keys():
                            oRe = oT["tradeReduced"]
                            iL = [j for j in range(cfg.posList.__len__()) if
                                  cfg.posList[j].account == accountID and cfg.posList[j].posID == oRe["tradeID"]]
                            i = int(iL[0])
                            v = cfg.posList[i].log.iloc[-1,].vol - abs(float(oRe["units"]))
                            p = oT["price"]
                            cp = float(oT["tradeReduced"]["realizedPL"])
                            comm = float(oT["commission"])
                            t = pd.Timestamp(oT["time"])
                            cfg.posList[i].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp, 'commission': comm}
                            if cfg.posList[i].log.loc[t].vol == 0:
                                cfg.posList[i].status = 'c'
                            cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[t] = float(oT["accountBalance"])
                            print(oRe)
                    print(ro)
        except V20Error:
            pass
        finally:
            pass

    def initPosLog(self, broker, accountID):
        if broker == 'backtest':
            pass
        if broker == "oanda":
            client = oandapyV20.API(access_token=cfg.brokerList['oanda']['token'])
            r = trades.OpenTrades(accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'])
            client.request(r)
            reply = dict(r.response)
            tList = reply["trades"]
            tList.reverse()
            for T in tList:
                ro = trades.TradeDetails(accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'],
                                         tradeID=T["id"])
                client.request(ro)
                reply = dict(ro.response)
                oT = reply["trade"]
                if not oT["instrument"] in cfg.pairList:
                    cfg.pairList.append(oT["instrument"])
                    cfg.pairList.sort()
                if float(oT["initialUnits"]) >= 0:
                    typePos = 'l'
                else:
                    typePos = 's'
                pList = [cfg.posList.index(p) for p in cfg.posList if
                         p.broker == 'oanda' and p.account == accountID and p.posID == oT["id"]]
                if pList == []:
                    cfg.posList.append(Position('oanda', accountID, oT["id"], oT["instrument"], float(oT["price"]),
                                                abs(float(oT["initialUnits"])), typePos, pd.Timestamp(oT["openTime"])))
                    pInd = -1
                else:
                    pInd = pList[0]
                cfg.posList[pInd].status = 'o'
                if "closingTransactionIDs" in oT.keys():
                    for cT in oT["closingTransactionIDs"]:
                        rc = trans.TransactionDetails(accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'],
                                                      transactionID=cT)
                        client.request(rc)
                        replyt = dict(rc.response)
                        if "tradeReduced" in replyt["transaction"].keys():
                            oRe = replyt["transaction"]["tradeReduced"]
                            v = cfg.posList[pInd].log.iloc[-1,].vol - abs(float(oRe["units"]))
                            p = replyt["transaction"]["price"]
                            cp = float(oRe["realizedPL"])
                            comm = float(replyt["transaction"]["commission"])
                            t = pd.Timestamp(replyt["transaction"]["time"])
                            cfg.posList[pInd].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp, 'commission': comm}
            # tstream = trans.TransactionsStream(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'])
            # cfg.brokerList['oanda']['accounts'][accountID]['tsv'] = client.request(tstream)

    def updatePosLog(self, broker, accountID):
        if broker == 'backtest':
            pass
        if broker == 'oanda':
            oT = dict(cfg.brokerList['oanda']['accounts'][accountID]['tsv'].__next__())
            print(oT)
            if oT["type"] == "ORDER_FILL":
                if "tradeOpened" in oT.keys():
                    oC = oT["tradeOpened"]
                    tempL = [o for o in cfg.posList if o.posID == oC["tradeID"]]
                    if tempL == []:
                        if not oT["instrument"] in cfg.pairList:
                            cfg.pairList.append(oT["instrument"])
                            cfg.pairList.sort()
                            client = oandapyV20.API(access_token=cfg.brokerList['oanda']['token'])
                            parstreamtrans = \
                                {
                                    "instruments": ",".join(cfg.pairList)
                                }
                            pstream = pricing.PricingStream(
                                accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'], params=parstreamtrans)
                            cfg.brokerList[broker]['psv'] = client.request(pstream)
                        if float(oC["units"]) >= 0:
                            typePos = 'l'
                        else:
                            typePos = 's'
                        cfg.posList.append(
                            Position('oanda', accountID, oC["tradeID"], oT["instrument"], float(oT["price"]),
                                     abs(float(oC["units"])), typePos, pd.Timestamp(oT["time"])))
                        cfg.posList[-1].status = 'o'
                        cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[pd.Timestamp(oT["time"])] = float(
                            oT["accountBalance"])
                if "tradesClosed" in oT.keys():
                    oCl = oT["tradesClosed"]
                    oCl.reverse()
                    for ocp in oCl:
                        iL = [j for j in range(cfg.posList.__len__()) if
                              cfg.posList[j].account == accountID and cfg.posList[j].posID == ocp["tradeID"]]
                        i = int(iL[0])
                        v = cfg.posList[i].log.iloc[-1,].vol - abs(float(ocp["units"]))
                        p = oT["price"]
                        cp = float(ocp["realizedPL"])
                        comm = float(oT["commission"]) / oCl.__len__()
                        t = pd.Timestamp(oT["time"])
                        cfg.posList[i].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp, 'commission': comm}
                        if cfg.posList[i].log.loc[t].vol == 0:
                            cfg.posList[i].status = 'c'
                        cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[t] = float(oT["accountBalance"])
                if "tradeReduced" in oT.keys():
                    oRe = oT["tradeReduced"]
                    iL = [j for j in range(cfg.posList.__len__()) if
                          cfg.posList[j].account == accountID and cfg.posList[j].posID == oRe["tradeID"]]
                    i = int(iL[0])
                    v = cfg.posList[i].log.iloc[-1,].vol - abs(float(oRe["units"]))
                    p = oT["price"]
                    cp = float(oT["tradeReduced"]["realizedPL"])
                    comm = float(oT["commission"])
                    t = pd.Timestamp(oT["time"])
                    cfg.posList[i].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp, 'commission': comm}
                    if cfg.posList[i].log.loc[t].vol == 0:
                        cfg.posList[i].status = 'c'
                    cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[t] = float(oT["accountBalance"])

    def initTick(self, broker, accountID):
        if broker == 'backtest':
            cfg.brokerList['backtest']['accounts'][accountID]['tickTable'] = pd.DataFrame(None)
            firstTickT = pd.to_datetime(
                str(cfg.brokerList['backtest']['iYear']) + '-' + str(cfg.brokerList['backtest']['iMonth']))
            for pair in cfg.pairList:
                filename = cfg.brokerList['backtest']['accounts'][accountID]['fileiter'][pair].__next__()
                file = pd.read_csv(os.path.join(cfg.brokerList['backtest']['path'], filename),
                                   index_col=0, parse_dates=True, usecols=[1, 2, 3], header=None)
                file = file.groupby(file.index, sort=False).mean()
                firstTickT = max(firstTickT, file.iloc[0].name)
                cfg.brokerList['backtest']['accounts'][accountID]['tickTable'] = \
                    pd.concat([cfg.brokerList['backtest']['accounts'][accountID]['tickTable'], file], axis=1)
            cfg.brokerList['backtest']['accounts'][accountID]['tickTable'].sort_index()
            cfg.brokerList['backtest']['accounts'][accountID]['tickTable'].columns = \
                pd.MultiIndex.from_product([cfg.pairList, ['ask', 'bid']])
            firstTickT = firstTickT.floor(str(cfg.history['gran']) + 'S') + pd.to_timedelta(cfg.history['gran'],
                                                                                            unit='S')
            firstTickV = cfg.brokerList['backtest']['accounts'][accountID]['tickTable'].loc[:firstTickT].fillna(
                method='ffill', axis=0).iloc[-1]
            firstTickT = firstTickV.name
            firstTickT = firstTickT
            buff = cfg.brokerList['backtest']['accounts'][accountID]['tickTable'].loc[
                   firstTickT:(firstTickT + pd.to_timedelta((cfg.history['length'] + 1) * cfg.history['gran'],
                                                            unit='S') - pd.to_timedelta(1))].fillna(method='ffill')
            buff = buff.copy()
            buff.loc[firstTickT] = firstTickV
            cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'] = buff
            cfg.brokerList['backtest']['accounts'][accountID]['tickTable'].drop(
                cfg.brokerList['backtest']['accounts'][accountID]['tickTable'].loc[
                :(firstTickT - pd.to_timedelta(1))].index.values)
            cfg.brokerList['backtest']['accounts'][accountID]['tickIter'] = \
                cfg.brokerList['backtest']['accounts'][accountID]['tickTable'].iterrows()
            for pair in cfg.pairList:
                cfg.history['predInput'][pair] = buff.loc[:, pair].agg('mean', axis=1).fillna(method='ffill').resample(
                    str(cfg.history['gran']) + 'S').ohlc()
                cfg.history['predInput'][pair].loc[:, 'close'] = cfg.history['predInput'][pair].loc[:, 'close'].fillna(
                    method='ffill')
                cfg.history['predInput'][pair] = cfg.history['predInput'][pair].fillna(method='bfill', axis=1)

        if broker == 'oanda':
            cfg.priceList['oanda']['accounts'][accountID] = pd.DataFrame(
                {'ask': [None for i in range(cfg.pairList.__len__())],
                 'bid': [None for i in range(cfg.pairList.__len__())],
                 'ts': [None for i in range(cfg.pairList.__len__())]},
                index=cfg.pairList)
            client = API(access_token=cfg.brokerList['oanda']['token'])
            r = accounts.AccountInstruments(accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'])
            rv = dict(client.request(r))
            instList = [inst["name"] for inst in rv["instruments"]]
            for ipair in cfg.priceList['oanda']['accounts'][accountID].index.tolist():
                if '_'.join([ipair[0:3], cfg.brokerList['oanda']['accounts'][accountID]['curr']]) not in instList:
                    if '_'.join([ipair[0:3], cfg.brokerList['oanda']['accounts'][accountID]['curr']]) in instList:
                        cfg.priceList['oanda']['accounts'][accountID].loc[
                            '_'.join([ipair[0:3], cfg.brokerList['oanda']['accounts'][accountID]['curr']])] = {
                            'ask': None,
                            'bid': None,
                            'ts': None}
                    elif '_'.join([cfg.brokerList['oanda']['accounts'][accountID]['curr'], ipair[0:3]]) in instList:
                        cfg.priceList['oanda']['accounts'][accountID].loc[
                            '_'.join([cfg.brokerList['oanda']['accounts'][accountID]['curr'], ipair[0:3]])] = {
                            'ask': None,
                            'bid': None,
                            'ts': None}
            parstreamtrans = \
                {
                    "instruments": ",".join(cfg.priceList['oanda']['accounts'][accountID].index)
                }
            r = pricing.PricingInfo(accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'],
                                    params=parstreamtrans)
            rv = dict(client.request(r))
            for ipair in rv["prices"]:
                p = ipair["instrument"]
                a = float(ipair["asks"][0]['price'])
                b = float(ipair["bids"][0]['price'])
                t = pd.Timestamp(ipair["time"])
                cfg.priceList['oanda']['accounts'][accountID].loc[p] = {'ask': a, 'bid': b, 'ts': t}
            # pstream = pricing.PricingStream(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'], params = parstreamtrans)
            # cfg.brokerList['oanda']['accounts'][accountID]['psv'] = client.request(pstream)

    def tick(self, broker, accountID):
        if broker == 'backtest':
            try:
                t, row = cfg.brokerList['backtest']['accounts'][accountID]['tickIter'].__next__()
                newRow = {}
                for pair in cfg.pairList:
                    if not pd.isna(row.loc[pair, 'ask']) and not pd.isna(row.loc[pair, 'bid']):
                        cfg.priceList['backtest']['accounts'][accountID].loc[pair] = {'ask': row.loc[pair, 'ask'],
                                                                                      'bid': row.loc[pair, 'bid'],
                                                                                      'ts': t}
                        newRow[pair] = (row.loc[pair, 'ask'] + row.loc[pair, 'bid']) / 2
                firstCandleT = t.floor(str(cfg.history['gran']) + 'S') - cfg.history['length'] * pd.to_timedelta(
                    cfg.history['gran'], unit='S')
                if cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'].iloc[-1].name < firstCandleT:
                    cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'].loc[firstCandleT] = \
                        cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'].iloc[-1]
                cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'] = \
                    cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'].fillna(method='ffill')
                cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'].drop(
                    cfg.brokerList['backtest']['accounts'][accountID]['histBuffer'].loc[
                    :(firstCandleT - pd.to_timedelta(1))].index.values)
                for pair in cfg.pairList:
                    cfg.history['predInput'][pair] = cfg.brokerList['backtest']['accounts'][accountID][
                                                         'histBuffer'].loc[firstCandleT:(
                                firstCandleT + (cfg.history['length'] + 1) * pd.to_timedelta(cfg.history['gran'],
                                                                                             unit='S')), pair].resample(
                        str(cfg.history['gran']) + 'S').ohlc()
            except StopIteration:
                pass

        if broker == 'oanda':
            client = oandapyV20.API(access_token=cfg.brokerList['oanda']['token'])
            parstreamtrans = \
                {
                    "instruments": ",".join(cfg.priceList['oanda']['accounts'][accountID].index)
                }
            r = pricing.PricingInfo(accountID=cfg.brokerList['oanda']['accounts'][accountID]['ID'],
                                    params=parstreamtrans)
            rv = dict(client.request(r))
            for ipair in rv["prices"]:
                p = ipair["instrument"]
                a = float(ipair["asks"][0]['price'])
                b = float(ipair["bids"][0]['price'])
                t = pd.Timestamp(ipair["time"])
                cfg.priceList['oanda']['accounts'][accountID].loc[p] = {'ask': a, 'bid': b, 'ts': t}
            # pS = dict(cfg.brokerList['oanda']['accounts'][accountID]['psv'].__next__())
            # print(pS)
            # if pS["type"] == "PRICE":
            #     p = pS["instrument"]
            #     a = float(pS["asks"][0]['price'])
            #     b = float(pS["bids"][0]['price'])
            #     t = pd.Timestamp(pS["time"])
            #     cfg.priceList['oanda'][accountID].loc[p] = {'ask': a, 'bid': b, 'ts': t}
            self.initPosLog(broker, accountID)
            rv = accounts.AccountSummary(cfg.brokerList['oanda']['accounts'][accountID]['ID'])
            client.request(rv)
            r = dict(rv.response)
            cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[
                cfg.priceList['oanda']['accounts'][accountID].ts.max()] = {
                'bal': float(r["account"]["balance"]),
                'NAV': float(r["account"]["NAV"]),
                'mused': float(0)}

    def histPrice(self, broker, accountID, pair, t0, t1=None, gran='M10'):
        if broker == 'backtest':
            pass
        if broker == 'oanda':
            t0Str = t0.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            if t1 == None:
                paramshist = \
                    {
                        "from": str(t0Str),
                        "granularity": gran
                    }
            else:
                t1Str = t1.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                paramshist = \
                    {
                        "from": str(t0Str),
                        "to": str(t1Str),
                        "granularity": gran
                    }
            priceH = pd.DataFrame({'c': [], 'h': [], 'l': [], 'o': []}, index=[])
            client = API(access_token=cfg.brokerList['oanda']['token'])
            for r in InstrumentsCandlesFactory(instrument=pair, params=paramshist):
                rv = dict(client.request(r))["candles"]
                for candle in rv:
                    print(candle)
                    priceH.loc[pd.Timestamp(candle["time"], tzinfo='UTC')] = candle["mid"]
            return (priceH)

    def execute(self, orders):
        for o in orders:
            if o['oType'] == 'o':
                self.open(o['broker'], o['account'], o['type'], o['pair'], o['vol'], o['price'], o['slip'])
            if o['oType'] == 'c':
                self.close(o['broker'], o['account'], o['pos'], o['vol'])


# %%
class Position(object):
    """

    """

    # transl = Translator()

    def __init__(self, broker, account, posID, pair, initPrice, initVol, typePos, t, stopLoss=0,
                 takeProfit=100000):  # Dictionary for pairs missing
        self.broker = broker
        self.account = account
        self.posID = posID
        self.status = 'w'  # w: waiting, o: open, c:close
        self.pair = pair
        self.initPrice = initPrice  # open price
        self.initVol = initVol  # initial position volume
        self.log = pd.DataFrame({'vol': [initVol], 'price': [initPrice], 'closedprof': [float(0)], 'commission': [0]},
                                index=[t])
        self.orderLog = pd.DataFrame({'volLeft': [initVol], 'price': [initPrice]}, index=[t])
        self.tradeVol = 0
        self.typePos = typePos  # l: long, s: short
        self.profit = 0  # result of position at instant t
        self.cost = 0
        # self.t = t #last ticket
        # self.entry = entryPos #price to enter position
        # self.exit = exitPos #price to exit position
        self.stopLoss = stopLoss  # hard coded stop loss broker side
        self.takeProfit = takeProfit  # hard coded take profit broker side
        # self.log = pd.Series([np.NaN, np.NaN],index = ['entry', 'exit'])

    def tick(self):
        if self.typePos == 'l':
            return (self.pl(cfg.priceList[self.broker]['accounts'][self.account].bid[self.pair]))
        if self.typePos == 's':
            return (self.pl(cfg.priceList[self.broker]['accounts'][self.account].ask[self.pair]))
        # if self.typePos == 'l':
        #     return(self.log.closedprof[-1] + self.tradeVol * cfg.priceList[self.broker][self.account].ask[self.pair])
        # if self.typePos == 's':
        #     return(self.log.closedprof[-1] - self.tradeVol * cfg.priceList[self.broker][self.account].bid[self.pair])

    def pl(self, p):
        if self.pair[-3:] == cfg.brokerList[self.broker]['accounts'][self.account]['curr']:
            conv = 1
        elif ('_').join([self.pair[-3:], cfg.brokerList[self.broker]['accounts'][self.account]['curr']]) in \
                cfg.priceList[self.broker]['accounts'][self.account].index:
            conv = cfg.priceList[self.broker]['accounts'][self.account].bid[
                ('_').join([self.pair[-3:], cfg.brokerList[self.broker]['accounts'][self.account]['curr']])]
        elif ('_').join([cfg.brokerList[self.broker]['accounts'][self.account]['curr'], self.pair[-3:]]) in \
                cfg.priceList[self.broker]['accounts'][self.account].index:
            conv = cfg.priceList[self.broker]['accounts'][self.account].ask[
                       ('_').join([cfg.brokerList[self.broker]['accounts'][self.account]['curr'], self.pair[-3:]])] ** (
                       -1)
        if self.typePos == 'l':
            return self.log.closedprof[-1] + (self.log.iloc[-1,].vol * (p - self.initPrice)) * conv
        if self.typePos == 's':
            return self.log.closedprof[-1] - (self.log.iloc[-1,].vol * (p - self.initPrice)) * conv

    # def closePos(self, vol):
    #     self.transl.close(self.broker, self.account, cfg.brokerList[self.broker]["token"], self, vol)

# % Temp
