import trade
import oandapyV20
import numpy as np
import pandas as pd

class Translator(object):
    """

    """

    def __init__(self, broker, accountID, token):
        self.broker = broker
        self.accountID = accountID
        self.token = token

    def open(self, type, pair, price, vol, slip):
        if self.broker == "oanda":
            if type == 'l':
                priceB = (1 - slip) * price
            if type == 's':
                priceB = (1 + slip) * price
            data = \
                {
                    "order": {
                        "units": str(vol),
                        "instrument": pair,
                        "timeInForce": "FOK",
                        "type": "MARKET",
                        "positionFill": "OPEN_ONLY",
                        "priceBound": str(priceB)
                    }
                }
            r = orders.OrderCreate(self.accountID, data = data)
            client.request(r)
            return(r.response)

    def close(self, pos, vol):
        if pos.broker == "oanda":
            if pos.status == 'w':
                r = orders.OrderCancel(accountID = self.accountID, orderID = posID)
                client.request(r)
                reply = dict(r.response)
                v = pos.orderLog.iloc[-1, 'volLeft']
                p = pos.orderLog.iloc[-1, 'price']
                t = pd.to_datetime(reply["orderCancelTransaction"]["time"])
                pos.orderLog.loc[t] = pd.DataFrame({'volLeft': v, 'price': p})
            if pos.status == 'o':
                data = \
                {
                    "units": str(vol)
                }
                r = trades.TradeClose(accountID = self.accountID, data = data)
                client.request(r)
                reply = dict(r.response)
                {'vol': 0}, {'price': initPrice}, {'closedprof': 0}, index = t
                v = pos.log.iloc[-1,].at['vol']-float(reply["OrderFillTransaction"]["units"])
                p = float(reply["OrderFillTransaction"]["price"])
                cp = pos.log.iloc[-1,].at['closedprofit'] + reply["OrderFillTransaction"]["pl"]
                t = reply["OrderFillTransaction"]["time"]
                pos.log.loc[t] = pd.DataFrame({'vol': v, 'price': p, 'closedprofit': cp)
            return(r.response)
