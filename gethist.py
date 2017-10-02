import krakenex
import datetime as dt
import time
import csv

#%%
k = krakenex.API()
k.load_key('/Users/fonsecamig/OneDrive/Documents/Miguel_OneDrive/MK/Forex/test/kraken.key')

#%%
pair = 'XXBTZUSD'

#%%
hist = []
lasttime = dt.datetime(1971, 1, 1, 0, 0, 9, 0)
lasttid = 0
while lasttime < dt.datetime(2016, 3, 31, 0, 0, 0, 0):
    histblock = dict(k.query_public('Trades',req = {'pair': pair, 'since': str(lasttid)}))
    time.sleep(10)
    for line in histblock['result'][pair]:
        hist.append(line)
        hist[-1][0] = float(hist[-1][0])
        hist[-1][1] = float(hist[-1][1])
#        hist[-1][2] = dt.datetime.utcfromtimestamp(hist[-1][2])
    lasttid = int(histblock['result']['last'])
    lasttime = dt.datetime.utcfromtimestamp(hist[-1][2])
    
    
#%%
filename = pair + '.csv'
with open(filename, 'w') as csvfile:
    fieldnames = ['price', 'vol', 'time']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for line in hist:
        writer.writerow({'price': line[0], 'vol': line[1], 'time': line[2]})