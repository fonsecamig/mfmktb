# use of the Trades{..} classes
import json
from oandapyV20 import API
from oandapyV20.contrib.requests import TradeCloseRequest

import oandapyV20.endpoints.trades as trades
import sys

def exampleAuth():
    accountID, token = None, None
    with open("oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

accountID, access_token = exampleAuth()

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
