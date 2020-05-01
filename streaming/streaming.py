import requests
import threading


def auth():
    accountID, token = None, None
    with open("../oanda/oanda.txt") as I:
        accountID = I.readline().strip()
        token = I.readline().strip()
    return accountID, token

def stream_transactions(r):
    for t in r.iter_lines():
        print(t)
    return

def stream_pricing(r):
    for p in r.iter_lines():
        print(p)
    return


accountID, access_token = auth()

url_main = 'https://stream-fxpractice.oanda.com/'

endpoint_transactions = url_main + '/v3/accounts/' + str(accountID) + '/transactions/stream'
endpoint_pricing = url_main + '/v3/accounts/' + str(accountID) + '/pricing/stream'

with requests.Session() as s:
    s.headers.update({'Authorization': 'Bearer ' + access_token})
    rt = s.get(endpoint_transactions, stream=True)
    rp = s.get(endpoint_pricing, params={'instruments': 'EUR_USD,EUR_GBP'}, stream=True)
    t_trans = threading.Thread(target=stream_transactions, args=(rt,))
    t_price = threading.Thread(target=stream_pricing, args=(rp,))
    t_trans.start()
    t_price.start()