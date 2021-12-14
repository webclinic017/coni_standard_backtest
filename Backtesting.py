import backtrader as bt
import backtrader.analyzers as btanalyzers
import numpy as np
import sys

'''
The Backtestor client is a wrapper around the Backtrader core engine that adds useful funcitonality including standard 
commission schemes, strategies, logging and notifications.
'''

# In this file the entire Backtrader logic is stored.
# Define new strategy classes to try something new

class Backtestor():
    #def backtest(data,asset, fromdate, todate, ma_fast, ma_slow, stop_loss, take_profit, show_plot= False, trailpercent=None, leverage=1, strategyName=None, sides=['LONG', 'SHORT']):
    def backtest(data, strategyName, strat_params, show_plot, opt_mode=False):
    #   IMPORTANT
        # params dict stores all required parameters and settings for the selected strategy.
        # When calling the Backtestor.backtest() function the user has to ensure that all required parameters for that
        # particular strategy are provided otherwise the the strategy will not execute."""


        class CommInfoFractional(bt.CommissionInfo):
            # This part is added to allow fractional positions which is usually the case for crypto trading:
            # https://www.backtrader.com/blog/posts/2019-08-29-fractional-sizes/fractional-sizes/
            def getsize(self, price, cash):
                '''Returns fractional size for cash operation @price'''
                return self.p.leverage * (cash / price)


        class StandardBaseStrategy(bt.Strategy):
            '''
            Base strategy class for coni project that extends the backtrader base strategy by adding notfication and
            logging functionality
            '''

            def __init__(self):
                # count rejected orders
                self.nr_rejectedorders = 0
                self.p_high = 0
                self.p_low = 9999999999999
                self.stop_loss_price = None
                self.take_profit_price = None

            def log(self, txt, asset, dt=None):
                ''' Logging function for this strategy'''
                dt = dt or self.datas[0].datetime.date(0)
                dt = self.datetime.datetime(ago=0)
                message = f'{dt.isoformat()},{asset},{txt}'
                # print(message)

            def notify_order(self, order):
                if order.status in [order.Canceled, order.Margin, order.Rejected]:
                    asset = self.data._name
                    self.log(f'Order Canceled/Margin/Rejected', asset=asset)
                    self.nr_rejectedorders += 1

                elif order.status in [order.Submitted, order.Accepted]:
                    # Buy/Sell order submitted/accepted to/by broker - Nothing to do
                    return

                # Check if an order has been completed
                # Attention: broker could reject order if not enough cash
                elif order.status in [order.Completed]:
                    asset = self.data._name
                    if order.isbuy():
                        self.log(f'BUY,size:{round(order.executed.size, 2)},price:{round(order.executed.price, 2)}',
                                 asset=asset)
                    elif order.issell():
                        self.log(f'SELL,size:{round(order.executed.size, 2)},price:{round(order.executed.price, 2)}',
                                 asset=asset)
                    self.bar_executed = len(self)

            def notify_trade(self, trade):
                asset = self.data._name
                if not trade.isclosed:
                    self.entryPrice = trade.price  # set entry price
                    self.p_high = trade.price  # init high value for stop_loss etc.
                    self.p_low = trade.price  # init low  value for stop_loss etc.
                    return
                self.log(f'PROFIT,GROSS:{round(trade.pnl, 2)},NET:{round(trade.pnlcomm, 2)}', asset=asset)

            def pre_next(self):
                print('pre next')

            def post_next(self):
                # A function that should be called after each next function of a strategy that implements stop loss
                print('post next')
                if self.data[0] > self.p_high:
                    self.p_high = self.data[0]
                if self.data[0] < self.p_low:
                    self.p_low = self.data[0]

            def stop(self):
                # Todo: Calculate Buy&Hold Benchmark here
                print("---------------------------------------------------------------------")
                print(f"Total rejected orders: {self.nr_rejectedorders}")



        class MaCrossStrategy(StandardBaseStrategy):
            '''
            parametize strategy based on function call parameters
            params will be accessable with self.params.XXX throughout backtesting (or alternatively self.p.XXX)
            '''

            if strategyName == 'MaCrossStrategy':
                params = (
                    ('ma_fast', strat_params['ma_fast']),
                    ('ma_slow', strat_params['ma_slow']),
                    ('leverage', strat_params['leverage'])
                )

            def __init__(self):
                super().__init__() # init the base strat
                # strategy indicators
                ma_fast = bt.ind.SMA(period=self.params.ma_fast)
                ma_slow = bt.ind.SMA(period=self.params.ma_slow)
                self.crossover = bt.ind.CrossOver(ma_fast, ma_slow)

                # To keep track of pending orders
                self.orders = None

            def next(self):
                # Check if an order is pending ... if yes, we cannot send a 2nd one
                if self.orders:
                    return

                if self.crossover > 0 or self.crossover < 0:
                    # TRADE
                    marketprice = self.data.close[0]
                    value = self.broker.getvalue()  # capital we have available
                    invest = value * self.p.leverage  # capital we use for our trade
                    if self.crossover > 0:
                        invest = invest # LONG
                    elif self.crossover < 0:
                        invest = -invest # SHORT

                    self.orders = self.order_target_value(target=invest)



        cerebro = bt.Cerebro()
        # Todo what the fuck is this :D
        #cerebro = bt.Cerebro(tradehistory=True, maxcpus=1, optreturn=True, optdatas=True, preload=True, runonce=True)

        # add data to the cerebro
        if 'assets' in strat_params.keys():
            for idx, asset in enumerate(strat_params['assets']):
                cerebro.adddata(data[idx], name=asset)
        elif 'asset' in strat_params.keys():
            cerebro.adddata(data, name=strat_params['asset'])

        if strategyName == 'MaCrossStrategy':
            cerebro.addstrategy(MaCrossStrategy)
        else:
            print('SELECT AN EXISTING STRATEGY OR IMPLEMENT NEW STRATEGY FIRST. :)')
            sys.exit()

        # Set the start cash
        startcash = 10000
        cerebro.broker.setcash(startcash)

        # Commision: allow fractional sizes, enable % commission on volume
        # 0.15% commission on volume as default value
        comminfo = CommInfoFractional(margin=False, commission=0.0015)
        cerebro.broker.addcommissioninfo(comminfo)

        # Add analyzers
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name = 'sharpe')
        cerebro.addanalyzer(btanalyzers.Transactions, _name = 'trans')
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name = 'trades')
        cerebro.addanalyzer(btanalyzers.AnnualReturn, _name = 'annual')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name = 'dd')

        # run cerebro (backtrader core engine)
        back = cerebro.run()

        # IF YOU RUN IN OPTIMIZATION MODE YOU RETURN THE RESULTS HERE
        #Todo: why?!
        # if opt_mode:
        #     return back

        if show_plot:
            cerebro.plot(show_plot=True, style='candlestick')

        # extract standard KPI results
        TOTAL_PNL = round(100 * ((cerebro.broker.getvalue() / startcash) - 1), 2)
        MAX_DD = round(back[0].analyzers.dd.get_analysis()["max"]["drawdown"], 2)
        try:
            SHARPE_RATIO = round(back[0].analyzers.sharpe.get_analysis()["sharperatio"], 2)
        except:
            SHARPE_RATIO = 0
        NR_TRADES = back[0].analyzers.trades.get_analysis()['total']['total']
        # print out annual returns
        d = back[0].analyzers.annual.get_analysis()
        for k, v in d.items():
            print(f"{k} : {round(v * 100, 2)}%")
        # Value of portfolio in time
        VALUE = back[0].observers.broker.value.get(ago=0, size=back[0].observers.broker.value.__len__())

        # return standard set of backtesting results
        return({'strategyName': strategyName,
                'strat_params':strat_params,
                'TOTAL_PNL':TOTAL_PNL,
                'MAX_DD':MAX_DD,
                'SHARPE_RATIO':SHARPE_RATIO,
                'NR_TRADES':NR_TRADES})
