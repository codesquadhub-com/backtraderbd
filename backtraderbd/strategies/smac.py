import backtrader as bt
from backtraderbd.strategies.base import BaseStrategy
from backtraderbd.settings import settings as conf

class SMACStrategy(BaseStrategy):
    """
    Simple moving average crossover strategy

    Parameters
    ----------
    fast_period : int
        The period used for the fast moving average line (should be smaller than `slow_upper`)
    slow_period : int
        The period used for the slow moving average line (should be larger than `fast_upper`)

    """
    name = conf.STRATEGY_PARAMS_SMAC_SYMBOL

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
        sma_fast = bt.ind.SMA(period=self.fast_period)  # fast moving average
        sma_slow = bt.ind.SMA(period=self.slow_period)  # slow moving average
        self.crossover = bt.ind.CrossOver(
            sma_fast, sma_slow
        )  # crossover signal

    def buy_signal(self):
        return self.crossover > 0

    def sell_signal(self):
        return self.crossover < 0
