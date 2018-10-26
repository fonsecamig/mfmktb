import os
import numpy as np
import scipy as sp
import pandas as pd
import json
import requests

root_path = os.getcwd()
data_path = os.path.join(root_path, 'data')
full_path = os.path.join(data_path, 'candles')
model_path = os.path.join(root_path, 'model02')

# pair_names = ['EURGBP', 'EURUSD', 'GBPUSD']
pair_names = ['AUDJPY', 'AUDNZD', 'AUDUSD', 'CADJPY', 'CHFJPY', 'EURCHF', 'EURGBP', 'EURJPY', 'EURUSD', 'GBPJPY',
              'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY']
i_year_train = 2017
i_month_train = 1
f_year_train = 2017
f_month_train = 12
i_year_eval = 2018
i_month_eval = 1
f_year_eval = 2017
f_month_eval = 3

model_nr = 0

price_type = 'm'
gran = 10
input_size = 6 * 60
output_size = 6 * 10
n1 = 10
w1 = len(pair_names) * input_size * 4 // 4
n2 = 5
w2 = len(pair_names) * output_size * 4
do_rate = 0.001
l_rate = 0.1
batch_size = 64
n_epochs = 5
shuffle_buffer_size = 50000

reg_df = pd.read_csv(os.path.join(model_path, 'reg.csv'), header=[0, 1], index_col=0)

seq_size = input_size + output_size

# http://host:port/v1/models/${MODEL_NAME}[/versions/${MODEL_VERSION}]:predict

input_vals = [np.random.multivariate_normal(mean=reg_df.loc[p, pd.IndexSlice[:, 'mean']],
                                                            cov=np.diag(reg_df.loc[p, pd.IndexSlice[:, 'sd']]),
                                                            size=input_size).reshape([1, input_size, 4]).tolist() for p in pair_names]
inputs = dict(zip(pair_names, input_vals))

input_data = json.dumps({'instances': [inputs]})

pred = requests.post('http://127.0.0.1:8501/v1/models/model:predict', data=input_data)


print(pred.json())
