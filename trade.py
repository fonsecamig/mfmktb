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

#%
class Translator(object):
    """

    """

    def __init__(self):
        pass

    def initAccount(self, broker, token, btpath = './', btfilelist = [], btcurr = 'USD', btamount = 100000, btmargin = 0.02, btstart = pd.Timestamp.now(tz = 'utc'), btend = pd.Timestamp('2000-01-01T00:00', tz = 'utc')):
        if broker == 'backtest': # Introduce pairs in config.py
            cfg.brokerList['backtest']['accounts'] = []
            cfg.brokerList['backtest'] = {'path': btpath, 'filelist': btfilelist}
            cfg.brokerList['backtest']['accounts'] = [{'ID': 0, 'tsv': None, 'psv': None,
                 'margin': btmargin,
                 'curr': btcurr,
                 'log': pd.Series([btamount], index=[btstart])}]
        if broker == 'oanda':
            client = oandapyV20.API(access_token = token)
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
                     'curr': rav["account"]["currency"], 'log': pd.Series([float(rav["account"]["balance"])], index = [pd.Timestamp.now(tz = 'utc')])})

    def open(self, broker, accountID, typeP, pair, vol, price, slip):
        try:
            if broker == "backtest":
                cfg.posList.append(
                    Position('backtest', accountID, 0, pair, price, vol, typeP, cfg.priceList['backtest'][0].loc[pair].ts))
                cfg.posList[-1].status = 'o'
                cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[cfg.priceList['backtest'][0]] = cfg.brokerList['backtest']['accounts'][accountID]['log'].iloc[-1] - price * vol
            if broker == "oanda":
                client = oandapyV20.API(access_token = cfg.brokerList['oanda']['token'])
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
                r = orders.OrderCreate(cfg.brokerList['oanda']['accounts'][accountID]['ID'], data = data)
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
                            cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[pd.Timestamp(oT["time"])] = float(oT["accountBalance"])
        finally:
            pass

    def close(self, broker, accountID, pos, vol):
        try:
            if vol <= cfg.posList[pos].log.iloc[-1,].at['vol']:
                if cfg.posList[pos].broker == "backtest":
                    if cfg.posList[pos].typePos == 'l':
                        tTrans = 'bid'
                    if cfg.posList[pos].typePos == 's':
                        tTrans = 'ask'
                    v = cfg.posList[pos].log.iloc[-1,].vol - vol
                    p = cfg.priceList['backtest'][0].loc[cfg.posList[pos].pair][tTrans]
                    cp = cfg.posList[pos].log.loc[-1].closedprof + v * p
                    comm = 0
                    t = cfg.priceList['backtest'][0].loc[cfg.posList[pos].pair][tTrans].ts
                    cfg.posList[pos].log.loc[t] = {'vol': v, 'price': p, 'closedprof': cp, 'commission': comm}
                    if cfg.posList[pos].log.loc[t].vol == 0:
                        cfg.posList[pos].status = 'c'
                    cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[t] = cfg.brokerList['backtest']['accounts'][accountID]['log'].iloc[-1] + cp
                if cfg.posList[pos].broker == "oanda":
                    client = oandapyV20.API(access_token = cfg.brokerList['oanda']['token'])
                    data = \
                    {
                        "units": str(vol)
                    }
                    r = trades.TradeClose(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'], tradeID = cfg.posList[pos].posID, data = data)
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
            client = oandapyV20.API(access_token = cfg.brokerList['oanda']['token'])
            r = trades.OpenTrades(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'])
            client.request(r)
            reply = dict(r.response)
            tList = reply["trades"]
            tList.reverse()
            for T in tList:
                ro = trades.TradeDetails(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'], tradeID=T["id"])
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
                pList = [cfg.posList.index(p) for p in cfg.posList if p.broker == 'oanda' and p.account == accountID and p.posID == oT["id"]]
                if pList == []:
                    cfg.posList.append(Position('oanda', accountID, oT["id"], oT["instrument"], float(oT["price"]), abs(float(oT["initialUnits"])), typePos, pd.Timestamp(oT["openTime"])))
                    pInd = -1
                else:
                    pInd = pList[0]
                cfg.posList[pInd].status = 'o'
                if "closingTransactionIDs" in oT.keys():
                    for cT in oT["closingTransactionIDs"]:
                        rc = trans.TransactionDetails(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'], transactionID = cT)
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
                            pstream = pricing.PricingStream(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'], params = parstreamtrans)
                            cfg.brokerList[broker]['psv'] = client.request(pstream)
                        if float(oC["units"]) >= 0:
                            typePos = 'l'
                        else:
                            typePos = 's'
                        cfg.posList.append(Position('oanda', accountID, oC["tradeID"], oT["instrument"], float(oT["price"]), abs(float(oC["units"])), typePos, pd.Timestamp(oT["time"])))
                        cfg.posList[-1].status = 'o'
                        cfg.brokerList['oanda']['accounts'][accountID]['log'].loc[pd.Timestamp(oT["time"])] = float(oT["accountBalance"])
                if "tradesClosed" in oT.keys():
                    oCl = oT["tradesClosed"]
                    oCl.reverse()
                    for ocp in oCl:
                        iL = [j for j in range(cfg.posList.__len__()) if cfg.posList[j].account == accountID and cfg.posList[j].posID == ocp["tradeID"]]
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
                    iL = [j for j in range(cfg.posList.__len__()) if cfg.posList[j].account == accountID and cfg.posList[j].posID == oRe["tradeID"]]
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
            cfg.brokerList['backtest']['accounts'][accountID]['psv'] = {}
            cfg.brokerList['backtest']['accounts'][accountID]['buffer'] = {}
            for pair in cfg.pairList:
                cfg.priceList['backtest']['accounts'][accountID]['log'] = pd.DataFrame({'ask': [None for i in range(cfg.pairList.__len__())],
                                                              'bid': [None for i in range(cfg.pairList.__len__())],
                                                              'ts': [None for i in range(cfg.pairList.__len__())]}, index = cfg.pairList)
            for file in cfg.brokerList['backtest']['filelist']:
                cfg.brokerList['backtest']['accounts'][accountID]['psv'][file] = csv.DictReader(open(cfg.brokerList['backtest']['path'] + file), fieldnames = ['pair', 'date', 'bid', 'ask'])
                cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file] = cfg.brokerList['backtest']['accounts'][accountID]['psv'][file].__next__()
                if cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[cfg.dct['backtest'][cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['pair']]].ts is None:
                    cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[cfg.dct['backtest'][cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['pair']]] = \
                        {
                            'ask':float(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['ask']),
                            'bid':float(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['bid']),
                            'ts': pd.Timestamp(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['date'])
                        }
                elif cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[cfg.dct['backtest'][cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['pair']]].ts < pd.Timestamp(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['date']):
                    cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[cfg.dct['backtest'][cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['pair']]] = \
                        {
                            'ask': float(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['ask']),
                            'bid': float(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['bid']),
                            'ts': pd.Timestamp(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['date'])
                        }
        if broker == 'oanda':
            cfg.priceList['oanda'][accountID] = pd.DataFrame({'ask': [None for i in range(cfg.pairList.__len__())],
                                                    'bid': [None for i in range(cfg.pairList.__len__())],
                                                    'ts': [None for i in range(cfg.pairList.__len__())]},
                                                   index = cfg.pairList)
            client = API(access_token = cfg.brokerList['oanda']['token'])
            parstreamtrans =\
            {
                "instruments": ",".join(cfg.pairList)
            }
            r = pricing.PricingInfo(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'], params = parstreamtrans)
            rv = dict(client.request(r))
            for ipair in rv["prices"]:
                p = ipair["instrument"]
                a = float(ipair["asks"][0]['price'])
                b = float(ipair["bids"][0]['price'])
                t = pd.Timestamp(ipair["time"])
                cfg.priceList['oanda'][accountID].loc[p] = {'ask': a, 'bid': b, 'ts': t}
            pstream = pricing.PricingStream(accountID = cfg.brokerList['oanda']['accounts'][accountID]['ID'], params = parstreamtrans)
            cfg.brokerList['oanda']['accounts'][accountID]['psv'] = client.request(pstream)

    def tick(self, broker, accountID):
        if broker == 'backtest':
            if cfg.brokerList['backtest']['accounts'][accountID]['psv'] != []:
                fN = pd.Series(
                    [pd.Timestamp(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][file]['date']) for file in
                     cfg.brokerList['backtest']['accounts'][accountID]['buffer']]).idxmin()
                try:
                    cfg.brokerList['backtest']['accounts'][accountID]['buffer'][fN] = \
                    cfg.brokerList['backtest']['accounts'][accountID]['psv'][fN].__next__()
                    cfg.brokerList['backtest']['accounts'][accountID]['log'].loc[
                        cfg.dct['backtest'][cfg.brokerList['backtest']['accounts'][accountID]['buffer'][fN]['pair']]] = \
                        {
                            'ask': float(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][fN]['ask']),
                            'bid': float(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][fN]['bid']),
                            'ts': pd.Timestamp(cfg.brokerList['backtest']['accounts'][accountID]['buffer'][fN]['date'])
                        }
                except StopIteration:
                    pass
        if broker == 'oanda':
            self.initTick(broker, accountID)
            # pS = dict(cfg.brokerList['oanda']['accounts'][accountID]['psv'].__next__())
            # print(pS)
            # if pS["type"] == "PRICE":
            #     p = pS["instrument"]
            #     a = float(pS["asks"][0]['price'])
            #     b = float(pS["bids"][0]['price'])
            #     t = pd.Timestamp(pS["time"])
            #     cfg.priceList['oanda'][accountID].loc[p] = {'ask': a, 'bid': b, 'ts': t}
            self.initPosLog(broker, accountID)

    def histPrice(self, broker, accountID, pair, t0, t1 = None, gran = 'M10'):
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
            priceH = pd.DataFrame({'c': [], 'h': [], 'l': [], 'o': []}, index = [])
            client = API(access_token = cfg.brokerList['oanda']['token'])
            for r in InstrumentsCandlesFactory(instrument = pair, params = paramshist):
                rv = dict(client.request(r))["candles"]
                for candle in rv:
                    print(candle)
                    priceH.loc[pd.Timestamp(candle["time"], tzinfo = 'UTC')] = candle["mid"]
            return(priceH)

    def execute(self, orders):
        for o in orders:
            if o['oType'] == 'o':
                self.open(o['broker'], o['account'], o['type'], o['pair'], o['vol'], o['price'], o['slip'])
            if o['oType'] == 'c':
                self.close(o['broker'], o['account'], o['pos'], o['vol'])


#%%
class Position(object):
    """

    """

    # transl = Translator()
    
    def __init__(self, broker, account, posID, pair, initPrice, initVol, typePos, t, stopLoss = 0, takeProfit = 100000): # Dictionary for pairs missing
        self.broker = broker
        self.account = account
        self.posID = posID
        self.status = 'w' #w: waiting, o: open, c:close
        self.pair = pair
        self.initPrice = initPrice #open price
        self.initVol = initVol #initial position volume
        self.log = pd.DataFrame({'vol': [initVol], 'price': [initPrice], 'closedprof': [float(0)], 'commission': [0]}, index = [t])
        self.orderLog = pd.DataFrame({'volLeft': [initVol], 'price': [initPrice]}, index = [t])
        self.tradeVol = 0
        self.typePos = typePos #l: long, s: short
        self.profit = 0 #result of position at instant t
        self.cost = 0
        # self.t = t #last ticket
        # self.entry = entryPos #price to enter position
        # self.exit = exitPos #price to exit position
        self.stopLoss = stopLoss #hard coded stop loss broker side
        self.takeProfit = takeProfit #hard coded take profit broker side
        # self.log = pd.Series([np.NaN, np.NaN],index = ['entry', 'exit'])


    def tick(self):
        return(self.pl(cfg.priceList[self.broker][self.account].ask[self.pair]))
        # if self.typePos == 'l':
        #     return(self.log.closedprof[-1] + self.tradeVol * cfg.priceList[self.broker][self.account].ask[self.pair])
        # if self.typePos == 's':
        #     return(self.log.closedprof[-1] - self.tradeVol * cfg.priceList[self.broker][self.account].bid[self.pair])

    def pl(self, p):
        if self.typePos == 'l':
            return(self.log.closedprof[-1] + self.tradeVol * p)
        if self.typePos == 's':
            return(self.log.closedprof[-1] - self.tradeVol * p)

    # def closePos(self, vol):
    #     self.transl.close(self.broker, self.account, cfg.brokerList[self.broker]["token"], self, vol)

#% Temp
