import pandas as pd
import numpy as np
import csv

#%%
pairlist = ['XXBTZGBP', 'XXBTZUSD', 'XETHZUSD', 'XETHZGBP']

filelist = [open('./kraken/' + pair + '.csv', 'r') for pair in pairlist]
count = dict(zip(pairlist, [sum(1 for line in file)-1 for file in filelist]))
for file in filelist: file.seek(0)
csvlist = dict(zip(pairlist, [csv.DictReader(file) for file in filelist]))
    
wfile = open('./kraken/kraken_joint.csv', 'w')
wcsv = csv.DictWriter(wfile, fieldnames = pairlist + ['time'])
wcsv.writeheader()

a = dict(zip(pairlist, [next(csvlist[pair]) for pair in pairlist]))
curridx = dict(zip(pairlist, [1 for x in pairlist]))
line = pd.Series(np.NaN, index = pairlist)
time = pd.Series(np.NaN, index = pairlist)
for pair in pairlist:
    line[pair], time[pair] = (np.NaN, a[pair]['time'])

#%%

while curridx != count:
    imin = time.min()
    ltime = list(time[time == imin].index)
    lline = line
    for l in ltime:
        a[l] = next(csvlist[l])
        line[l] = a[l]['price']
        lline[l] = a[l]['price']
        curridx[l] += 1
        if curridx[l] < count[l]:
            time[l] = a[l]['time']
    
    w = dict(zip(pairlist + ['time'], list(line) + [a[ltime[0]]['time']]))
    wcsv.writerow(w)
    for l in ltime:
        if curridx[l] == count[l]:
            time = time.drop(l)
            line[l] = np.NaN

#%%
for file in filelist: file.close()
wfile.close()
