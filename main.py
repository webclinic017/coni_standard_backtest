
import backtrader as bt
import backtrader.analyzers as btanalyzers
#from BACKTRADER_strategies import MaCrossStrategy

import matplotlib
import plotly
import pprint

from datetime import datetime
import time # to analyse program execution time
import numpy as np
import pandas as pd
import pickle
import json
import psutil
import os
import sys
import inspect

from binance.client import Client
import requests
from Databutler import databutler

import matplotlib.pyplot as plt

# import backtests including strageties
from Backtesting import Backtestor as btor
from Helpers import Helper as helper


#  --------  MAIN ---------
# MAIN #
# Define parameter for backtesting scan
# parameters which are None may not apply or will be varied each backtest
binanceClient = Client("", "")
BT_params_fixed = {
    'strategyName': 'MaCrossStrategy',
    'leverage': 0.95,
    'sides': ['LONG', 'SHORT'],  # we want to go LONG and SHORT
    'asset': 'ETHUSDT',
    'ma_fast': 13,
    'ma_slow': 21,
    'fromdate': datetime(2021, 12, 1),  # [yyyy, (m)m, (d)d]     # BE CAREFUL WITH CSV IMPORT: DATE MAY NOT APPLY
    'todate': datetime(2021, 12, 13),  # BE CAREFUL WITH CSV IMPORT: DATE MAY NOT APPLY
    'interval': binanceClient.KLINE_INTERVAL_1HOUR,
    'price_multiplier': 1,
    'data_source': 'BINANCE'  # available: YAHOO (interval ignored), BINANCE (all intervals), CSV
}

if (not BT_params_fixed['interval'] == binanceClient.KLINE_INTERVAL_1DAY) and (BT_params_fixed['data_source']=='YAHOO'):
    print('NOT POSSIBLE: TAKE THE DATA FROM BINANCE')
    sys.exit()

#  ACQUIRE DATA--------------------------------------------------------------------------------------------------------
mybutler = databutler(directory='Datafeeds/') #initiates databutler object

# define which data we want the butler to fetch
data_params = {'asset': BT_params_fixed['asset'],
               'fromdate':BT_params_fixed['fromdate'],
               'todate': BT_params_fixed['todate'],
               'interval': BT_params_fixed['interval'],
               'price_multiplier': BT_params_fixed['price_multiplier'],
               'data_source': BT_params_fixed['data_source']}

# get data through butler
data = mybutler.get_data(data_params=data_params)

# create results by iterating through specified tests
results = {}
results['test_results'] = []  # list for test_result dicts
n_test = 0

strat_params = {'ma_fast': BT_params_fixed['ma_fast'],
                'ma_slow': BT_params_fixed['ma_slow'],
                'sides': BT_params_fixed['sides'],
                'leverage': BT_params_fixed['leverage'],
                'asset': BT_params_fixed['asset']}

# start the test
sim_result = btor.backtest(data=data,
                           strategyName=BT_params_fixed['strategyName'],
                           strat_params=strat_params,
                           show_plot=False,
                           opt_mode= False) #Todo: whats that?


hlp = helper()
filename = hlp.save_results(result=sim_result, BT_params_fixed=BT_params_fixed)

results_loaded = hlp.load_results(filename=filename)
5
