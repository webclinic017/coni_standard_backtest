from binance.client import Client
from yaspin import yaspin
import os.path
from datetime import datetime
import pickle
import pandas as pd
import backtrader as bt

class databutler():

    def __init__(self,directory):
        #binance client without keys for data acquisition
        self.binanceClient = Client("", "")
        #directory in project folder for data storage
        self.directory = directory
        #data source

    def get_data(self,data_params):
        if data_params['data_source'] == 'BINANCE':
            data = self.get_data_BINANCEAPI(data_params = data_params)
        elif data_params['data_source'] == 'YAHOO':
            data = self.get_data_Yahoo(data_params=data_params)
        elif data_params['data_source'] == 'CSV':
            data = self.get_data_CSV(data_params=data_params)
        return data

    def get_data_BINANCEAPI(self,data_params):
        spinner = yaspin()  # loading visualization

        data_details = [data_params['asset'], data_params['interval'],
                        str(data_params['fromdate'].timestamp()), str(data_params['todate'].timestamp())]
        file_ID = data_details[0] + '_' + data_details[1] + '_' + str(datetime.fromtimestamp(float(data_details[2])))[
                                                                  0:10] + '_' + str(
            datetime.fromtimestamp(float(data_details[3])))[0:10]
        print(f'Data: {file_ID}')
        filepath = self.directory + 'Binance_API/' + file_ID + '.dat'
        if os.path.isfile(filepath):
            print('Data already downloaded. Loading it.')
            with open(filepath, 'rb') as f:
                data = pickle.load(f)

        else:
            spinner.text = f'Downloading data from Binance...'
            spinner.start()
            klines = self.binanceClient.get_historical_klines(*data_details)
            klines_df = pd.DataFrame(klines)
            col_names = ['open time', 'open', 'high', 'low', 'close', 'volume', 'close time', 'quote asset volume',
                         'number of trades', 'taker buy base asset volume', 'taker buy quote asset volume',
                         'Can be ignored(see docu)']
            klines_df.columns = col_names
            spinner.stop()

            for col in col_names:
                klines_df[col] = klines_df[col].astype(float)
            klines_df['datetime'] = pd.to_datetime(klines_df['open time'] * 1000000, infer_datetime_format=True)
            klines_df = klines_df.drop(
                ['open time', 'close time', 'quote asset volume', 'number of trades', 'taker buy base asset volume',
                 'taker buy quote asset volume', 'Can be ignored(see docu)'], axis=1, errors='ignore')
            klines_df = klines_df.set_index('datetime')

            # Price multiply
            klines_df['open'] = klines_df['open'] * data_params['price_multiplier']
            klines_df['high'] = klines_df['high'] * data_params['price_multiplier']
            klines_df['low'] = klines_df['low'] * data_params['price_multiplier']
            klines_df['close'] = klines_df['close'] * data_params['price_multiplier']

            # reformat as backtrader datafeed
            data = bt.feeds.PandasData(dataname=klines_df)

            # save data
            print('Saving data.')
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)

        return data

    def get_data_CSV(self,data_params):
        print('not implemented.')
        pass

    def get_data_Yahoo(self,data_params):
        data = bt.feeds.YahooFinanceData(dataname=data_params['asset'], fromdate=data_params['fromdate'], todate=data_params['todate'])
        return data

