import pandas as pd
import numpy as np
import csv

#%%
    
#%%
filename = '.csv'
with open(filename, 'r') as csvfile:
    reader = csv.DictReader(csvfile, fieldnames=fieldnames)
    for line in hist:
        writer.writerow({'price': line[0], 'vol': line[1], 'time': line[2]})