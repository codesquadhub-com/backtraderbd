import backtrader as bt
from backtraderbd.strategies.base import BaseStrategy
from backtraderbd.settings import settings as conf

class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) trading strategy

    Parameters
    ----------
    rsi_period : int
        Period used as basis in computing RSI
    rsi_upper : int
        The RSI upper limit, above which the assess is considered "overbought" and is sold
    rsi_lower : int
        The RSI lower limit, below which the assess is considered "oversold" and is bought
    """

    name = conf.STRATEGY_PARAMS_RSI_SYMBOL

    params = (("rsi_period", 14), ("rsi_upper", 70), ("rsi_lower", 30))

    def __init__(self):

        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.rsi_period = self.params.rsi_period
        self.rsi_upper = self.params.rsi_upper
        self.rsi_lower = self.params.rsi_lower
        print("===Strategy level arguments===")
        print("rsi_period :", self.rsi_period)
        print("rsi_upper :", self.rsi_upper)
        print("rsi_lower :", self.rsi_lower)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.rsi_period)

    def buy_signal(self):
        return self.rsi[0] < self.rsi_lower

    def sell_signal(self):
        return self.rsi[0] > self.rsi_upper