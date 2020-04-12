import backtrader as bt
from backtraderbd.strategies.base import BaseStrategy
from backtraderbd.settings import settings as conf

class MATrendStrategy(BaseStrategy):
    """
    If short ma > long ma, then go to long market, else, go to short market.
    Attributes:
        sma_s(DataFrame): short term moving average.
        sma_l(DataFrame): long term moving average.
    """

    name = conf.STRATEGY_PARAMS_MA_SYMBOL

    params = dict(
        ma_periods=dict(
            ma_period_s=15,
            ma_period_l=60,
            stock_id='0'
        )
    )

    def __init__(self):

        # Initialize global variables
        super().__init__()

        self.sma_s = bt.indicators.MovingAverageSimple(
            self.datas[0], period=self.params.ma_periods.get('ma_period_s')
        )
        self.sma_l = bt.indicators.MovingAverageSimple(
            self.datas[0], period=self.params.ma_periods.get('ma_period_l')
        )


    def buy_signal(self):
        return self.sma_s[0] > self.sma_l[0]

    def sell_signal(self):
        return self.sma_s[0] <= self.sma_l[0]