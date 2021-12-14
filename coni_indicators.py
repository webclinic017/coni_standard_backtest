import backtrader as bt
import backtrader.indicators as btind
import math

'''
Custom written indicators for the coni project
'''

#Volatility derived from bollinger band gap
class BBvola(bt.Indicator):
    lines = ('volatility','vola_level')
    params = (('period', 13), ('devfactor', 2),)

    def __init__(self):
        #
        self.addminperiod(self.params.period)

        #create bollingerbands indicator
        bbands = btind.BollingerBands(self.data, period = self.params.period, devfactor = self.p.devfactor)

        #calculate volatility as bandgap divided by close price
        self.lines.volatility = (bbands.lines.top-bbands.lines.bot)/self.data

#calculates an adapting moving average as a function of a volatility level
#Inputs: 1) klines, 2) some parameters as described below, 3) a volatility indicator
class SMAvola(bt.Indicator):

    #SMAvol line provides todays moving average using a period that is a function of the volatility
    #Current_period line tells the moving average period that was used on that particular candle
    lines = ('SMAvola','current_period')

    #parameter 'inertia' tells how flexible the SMA period is, how fast it changes with a change in volatility
    #parameter 'SMA_central' tells what the central value for the period is around which the period oscillates
    #parameter 'SMA_min' and 'SMA_max' indicate minimum and maximum values that can be reached by the period
    #parameter 'vola_average' refers to the volatility reference point relative to which high- and low-vola are measured
    params = (('inertia', 1), ('SMA_min', 8), ('SMA_max', 16), ('vola_average',1), ('vola', BBvola),)

    def __init__(self):

        #set minimum required period to longest SMA period that can be achieved
        self.addminperiod(self.params.SMA_max)

        #get volatility values using volatility indicator
        #here the BBvola indicator is imported and executed on the dataline that is fed into SMAvola
        #period = self.params.SMA_central might be too slow --> choose self.params.SMA_central/2 ?
        #                                                   --> or will be adjustable through inertia factor anyways?

        SMA_central = round((self.p.SMA_max+self.p.SMA_min)/2)

        #IMPORTANT, to maintain a useful reference value for the volatility this period should be kept constant.
        self.vola = self.p.vola(self.data,period = 14, devfactor = 2)


    def next(self):
        #read out volatility value at current candle
        vola_now = self.vola[0]

        #calculate period based on volatility value
        def vola2period(vola,vola_average,SMA_min,SMA_max,inertia):

            # adjust this function for different relationship or include different types of relationships
            current_period = SMA_min + ((SMA_max-SMA_min)/(1+math.exp(-inertia*(vola-vola_average))))

            return current_period

        self.lines.current_period[0] = vola2period(vola = vola_now,
                                 vola_average=self.params.vola_average,
                                 SMA_min = self.params.SMA_min,
                                 SMA_max = self.params.SMA_max,
                                 inertia= self.params.inertia)


        #calculate SMA value based on current_period value
        datasum = math.fsum(self.data.get(size=round(self.lines.current_period[0])))
        self.lines.SMAvola[0] = datasum / round(self.lines.current_period[0])

class partial_trend(bt.Indicator):

    # This indicator tells whether the current price is the maximum or minimum price within the last N=period candles.
    # In these cases trend = long or short respectively
    # If neither or these is the case, trend = neutral

    # trend line indicates whether this partial_trend bot is currently long,short or neutral
    lines = ('trend',)

    # period param defines how far the indicator looks back
    params = (('period', 2), )

    def __init__(self):
        #set minimum required period to period of this partial_trend bot
        self.addminperiod(self.params.period)

        self.maxV = bt.ind.MaxN(period=self.p.period)
        self.minV = bt.ind.MinN(period=self.p.period)

    def next(self):
        if self.data[0] == self.maxV[0]:
            self.lines.trend[0] = 1
        elif self.data[0] == self.minV[0]:
            self.lines.trend[0] = -1
        else:
            self.lines.trend[0] = 0

class partial_trend2(bt.Indicator):

    # This indicator tells whether the current price is the maximum or minimum price within the last N=period candles.
    # In these cases trend = long or short respectively
    # If neither or these is the case, trend = neutral

    # IMPORTANT: due to its recursive nature this indicator might not work properly for timeframe-mixing

    # trend line indicates whether this partial_trend bot is currently long,short or neutral
    lines = ('trend',)

    # period param defines how far the indicator looks back
    params = (('period', 2), ('buffer_perc', 0.03), )

    def __init__(self):
        self.entry_price = 0

        self.maxV = bt.ind.MaxN(period=self.p.period)
        self.minV = bt.ind.MinN(period=self.p.period)

    def next(self):
        # calculate relative price change from last entry for stop-loss
        if self.entry_price != 0:
            self.delta_price = (self.data[0] - self.entry_price) / self.entry_price

        # on starting day bot is in status NEUTRAL
        if len(self)==self.p.period:
            self.lines.trend[0] = 0

        # Coming from NEUTRAL
        elif self.lines.trend[-1] == 0:
            if self.data[0] == self.maxV[0]:
                # switch to LONG
                self.lines.trend[0] = 1
                self.entry_price = self.data[0]
            elif self.data[0] == self.minV[0]:
                # switch to SHORT
                self.lines.trend[0] = -1
                self.entry_price = self.data[0]
            else:
                # stay NEUTRAL
                self.lines.trend[0] = 0
                self.entry_price = 0

        # Coming from SHORT
        elif self.lines.trend[-1] == -1:
            if self.data[0] == self.maxV[0]:
                # switch to LONG
                self.lines.trend[0] = 1
                self.entry_price = self.data[0]
            elif self.delta_price > self.p.buffer_perc:
                # Stoploss, go back to NEUTRAL
                self.lines.trend[0] = 0
                self.entry_price = 0
                #print('STOP LOSS ACTIVATED, going back to neutral')
            else:
                # stay SHORT
                self.lines.trend[0] = -1

        # Coming from LONG
        elif self.lines.trend[-1] == 1:
            if self.data[0] == self.minV[0]:
                # switch to SHORT
                self.lines.trend[0] = -1
                self.entry_price = self.data[0]
            elif self.delta_price < -self.p.buffer_perc:
                # Stoploss, go back to NEUTRAL
                self.lines.trend[0] = 0
                self.entry_price = 0
                #print('STOP LOSS ACTIVATED, going back to neutral')
            else:
                # stay LONG
                self.lines.trend[0] = 1

class maxbot_sizer(bt.Indicator):
    # this indicator directly provides the position output for a list of partial_trend (v1 and v2) indicators

    lines = ('position',)
    params = (('periods', [2,5,10]),)

    def __init__(self):
        # initialize partial bots
        self.bots = []
        for period in self.p.periods:
            #thisbot = partial_trend2(period=period, buffer_perc = 0.005, subplot = True)
            thisbot = partial_trend(period=period, subplot=False)
            self.bots.append(thisbot)

    def next(self):
        target = 0
        for bot in self.bots:
            target = target + bot.lines.trend[0]

        self.lines.position[0] = (target / len(self.bots))