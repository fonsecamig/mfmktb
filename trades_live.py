# use of the Trades{..} classes
import json
from oandapyV20 import API
from oandapyV20.contrib.requests import TradeCloseRequest
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.transactions as trans
import oandapyV20.endpoints.pricing as pricing

import sys

def auth():
    accountID, token = None, None
    with open("./oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

accountID, access_token = auth()

import oandapyV20.endpoints.pricing as pricing

print(sys.argv)

chc = sys.argv[1]

api = API(access_token=access_token)

if chc == 'list':
   r = trades.TradesList(accountID)
   rv = api.request(r)
   print("RESP:\n{} ".format(json.dumps(rv, indent=2)))

if chc == 'open':
   r = trades.OpenTrades(accountID)
   rv = api.request(r)
   print("RESP:\n{} ".format(json.dumps(rv, indent=2)))
   tradeIDs = [o["id"] for o in rv["trades"]]
   print("TRADE IDS: {}".format(tradeIDs))

if chc == 'details':
   for O in sys.argv[2:]:
       r = trades.TradeDetails(accountID, tradeID=O)
       rv = api.request(r)
       print("RESP:\n{} ".format(json.dumps(rv, indent=2)))

if chc == 'close':
   X = iter(sys.argv[2:])
   for O in X:
       #cfg = { "units": X.__next__() }
       cfg = TradeCloseRequest(units=X.__next__())
       r = trades.TradeClose(accountID, tradeID=O, data=cfg.data)
       rv = api.request(r)
       print("RESP:\n{} ".format(json.dumps(rv, indent=2)))

if chc == 'cltext':
   for O in sys.argv[2:]:  # tradeIDs
       cfg = { "clientExtensions": {
               "id": "myID{}".format(O),
               "comment": "myComment",
            }
         }
       r = trades.TradeClientExtensions(accountID, tradeID=O, data=cfg)
       rv = api.request(r)
       print("RESP:\n{} ".format(json.dumps(rv, indent=2)))

if chc == 'crc_do':
   X = iter(sys.argv[2:])
   for O in X:
       cfg = {
               "takeProfit": {
                 "timeInForce": "GTC",
                 "price": X.next(),
               },
               "stopLoss": {
                 "timeInForce": "GTC",
                 "price": X.next()
               }
         }
       r = trades.TradeCRCDO(accountID, tradeID=O, data=cfg)
       rv = api.request(r)
       print("RESP:\n{} ".format(json.dumps(rv, indent=2)))

if chc == 'streamprice':
    params =\
        {
            "instruments": "EUR_USD,EUR_JPY"
        }
    r = pricing.PricingStream(accountID=accountID, params=params)
    rv = api.request(r)
    maxrecs = 10
    for ticks in rv:
        maxrecs -= 1
        print(json.dumps(ticks, indent=4), ",")
        if maxrecs == 0:
            # r.terminate("maxrecs records received")
            break

if chc == 'streamtrans':
    params = {"instruments": "EUR_USD,EUR_JPY"}
    r = trans.TransactionsStream(accountID=accountID)
    rv = api.request(r)
    maxrecs = 5
    try:
        for T in r.response:  # or rv ...
            print(json.dumps(T, indent=4), ",")
            maxrecs -= 1
            if maxrecs == 0:
                r.terminate("Got them all")
    except trans.StreamTerminated as e:
        print("Finished: {msg}".format(msg=e))

