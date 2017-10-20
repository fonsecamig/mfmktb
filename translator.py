import oandapyV20

class Translator(object):
    """

    """

    def __init__(self, broker, accountID, token):
        self.broker = broker
        self.accountID = accountID
        self.token = token

    def open(self, type, pair, price, vol, slip):
        if self.broker = "oanda":
            if type = 'l':
                priceB = (1 - slip) * price
            if type = 's':
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

    def close(self, pos):
        if pos.broker = "oanda":
            if pos.status = 'w':
                orders.OrderCancel(accountID = self.accountID, orderID = posID)
                client.request(r)
                return (r.response)
            if pos.status = 'o':
                data = \
                {
                    "units": str(vol)
                }
                r = trades.TradeClose(accountID = self.accountID, data = data)
                client.request(r)
                print(r.response)
