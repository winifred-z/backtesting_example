from backtesting import Backtest, Strategy
from backtesting.test import GOOG
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
import seaborn as sns
import matplotlib.pyplot as plt
import talib

#print(GOOG)

def optim_func(series):
    #make most money while being in market least amount of time
    opt1 = series["Equity Final [$]"]/series["Exposure Time [%]"]
    if series["# Trades"] < 10:
        return -1
    return opt1

class RsiOscillator(Strategy):

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    position_size = 1

    def init(self):
        #build indicator
        #talib.RSI is pre-built talib indicator
        self.daily_rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)
        self.weekly_rsi = resample_apply("W-FRI", talib.RSI, self.data.Close, self.rsi_window)

    def next(self):
        price = self.data.Close[-1]

        #trades on 3 days after crossover (RSI < upper bound)
        if self.weekly_rsi[-1] > self.upper_bound and barssince(self.daily_rsi < self.upper_bound) == 3:
        #and crossover(self.daily_rsi, self.upper_bound):
            if self.position.is_long:
                print(self.position.size)
                print(self.position.pl_pct)
                self.position.close()
                self.sell()

        elif crossover(self.lower_bound, self.daily_rsi) and self.weekly_rsi[-1] < self.lower_bound:
            #every time theres a crossover, buy x shares
            self.buy(size=self.position_size) 
            '''
            #stop loss, no more than 5% loss
            #buy when more than 15% profit
            self.buy(tp=1.15*price, sl= 0.95*price)

            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()
            '''

        #buy everytime RSI low
        elif self.lower_bound > self.daily_rsi[-1]:
            self.buy(size=self.position_size)

bt = Backtest(GOOG, RsiOscillator, cash = 10_000)
stats, heatmap = bt.optimize(
        upper_bound = range(55,85,5),
        lower_bound = range(10,45,5),
        rsi_window = 14, #range(10,30,1),
        maximize = "Sharpe Ratio",
        constraint = lambda param: param.upper_bound > param.lower_bound,
        return_heatmap= True
        #max_tries = 100 <- reduces chance of overfitting + runtime
)

#print(heatmap)
#plot_heatmaps(heatmap, agg = "mean")


'''
#Seaborn heatmap:
#unique combinations of upper + lower bounds
hm = heatmap.groupby(["upper_bound", "lower_bound"]).mean().unstack()
sns.heatmap(hm, cmap="plasma")
plt.show()
print(hm)
'''

#print(stats)
print(stats['_trades'].to_string())

lower_bound = stats["_strategy"].lower_bound
bt.plot(filename = f'plots/plot-{lower_bound}.html')