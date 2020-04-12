import backtrader as bt
from backtraderbd.strategies.base import BaseStrategy
from backtraderbd.settings import settings as conf

class EMACStrategy(BaseStrategy):
    """
    Exponential moving average crossover strategy

    Parameters
    ----------
    fast_period : int
        The period used for the fast exponential moving average line (should be smaller than `slow_upper`)
    slow_period : int
        The period used for the slow exponential moving average line (should be larger than `fast_upper`)

    """
    name = conf.STRATEGY_PARAMS_EMAC_SYMBOL

    params = (
        ("fast_period", 10),  # period for the fast moving average
        ("slow_period", 30),
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.fast_period = self.params.fast_period
        self.slow_period = self.params.slow_period

        print("===Strategy level arguments===")
        print("fast_period :", self.fast_period)
        print("slow_period :", self.slow_period)
        ema_fast = bt.ind.EMA(period=self.fast_period)  # fast moving average
        ema_slow = bt.ind.EMA(period=self.slow_period)  # slow moving average
        self.crossover = bt.ind.CrossOver(
            ema_fast, ema_slow
        )  # crossover signal

    def buy_signal(self):
        return self.crossover > 0

    def sell_signal(self):
        return self.crossover < 0