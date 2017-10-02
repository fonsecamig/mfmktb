import pandas as pd
import numpy as np
import csv

#%%
pairlist = ['XXBTZGBP', 'XXBTZUSD', 'XETHZUSD', 'XETHZGBP']

filelist = [open(pair + '.csv', 'r') for pair in pairlist]
count = dict(zip(pairlist, [sum(1 for line in file)-1 for file in filelist]))
for file in filelist: file.seek(0)
csvlist = dict(zip(pairlist, [csv.DictReader(file) for file in filelist]))

a = dict(zip(pairlist, [next(csvlist[pair]) for pair in pairlist]))
curridx = dict(zip(pairlist, [1 for x in pairlist]))
line = pd.Series(np.NaN, index = pairlist)
time = pd.Series(np.NaN, index = pairlist)
for pair in pairlist:
    line[pair], time[pair] = (np.NaN, a[pair]['time'])

imin = time.argmax()
line[imin] = a[pair]['price']

wfile = open('kraken_joint.csv', 'w')
wcsv = csv.DictWriter(wfile, fieldnames = pairlist + ['time'])
wcsv.writeheader()

while curridx != count:
    imin = time.argmin()
    a[imin] = next(csvlist[imin])
    w = dict(zip(pairlist + ['time'], list(line) + [a[pair]['time']]))
    wcsv.writerow(w)
    line[imin] = a[imin]['price']
    curridx[imin] += 1
    if curridx[imin] == count[imin]:
        time = time.drop(imin)
        line[imin] = np.NaN
    else:
            time[imin] = a[imin]['time']
    
for file in filelist: file.close()
wfile.close()