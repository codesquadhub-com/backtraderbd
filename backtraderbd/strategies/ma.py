import datetime as dt
import backtrader as bt

from backtraderbd.strategies.base import BaseStrategy
import backtraderbd.data.bdshare as bds
import backtraderbd.strategies.utils as bsu
from backtraderbd.settings import settings as conf
from backtraderbd.libs.log import get_logger

logger = get_logger(__name__)

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
        self.order = None

        self.sma_s = bt.indicators.MovingAverageSimple(
            self.datas[0], period=self.params.ma_periods.get('ma_period_s')
        )
        self.sma_l = bt.indicators.MovingAverageSimple(
            self.datas[0], period=self.params.ma_periods.get('ma_period_l')
        )


    def start(self):
        logger.debug('>Starting strategy, ma_period_s is %d, ma_period_l is %d' % (
            self.params.ma_periods.get('ma_period_s'),
            self.params.ma_periods.get('ma_period_l')
        ))

    def next(self):

        if self.order:
            return

        if not self.position:
            if self.sma_s[0] > self.sma_l[0]:
                # Using the current close price to calculate the size to buy, but use
                # the next open price to executed, so it is possible that the order
                # can not be executed due to margin, so set the target to 0.8 instead
                # of 1.0 to reduce the odds of not being executed
                target_long = 0.8
                self.order = self.order_target_percent(target=target_long, valid=bt.Order.DAY)
                if self.datas[0].datetime.date() == dt.datetime.now().date() - dt.timedelta(days=1):
                    stock_id = self.params.ma_periods.get('stock_id')
                    action = 'buy'
                    bsu.Utils.log(
                        self.datas[0].datetime.date(),
                        f'Market Signal: stock {stock_id}, action: {action}, '
                        f'adjust position to {target_long:.2f}')
                    symbol = dt.datetime.now().strftime('%Y-%m-%d')
                    bsu.Utils.write_daily_alert(symbol, stock_id, action)
        else:
            if self.sma_s[0] <= self.sma_l[0]:
                target_short = 0.0
                self.order = self.order_target_percent(target=target_short, valid=bt.Order.DAY)
                if self.datas[0].datetime.date() == dt.datetime.now().date() - dt.timedelta(days=1):
                    stock_id = self.params.ma_periods.get('stock_id')
                    action = 'sell'
                    bsu.Utils.log(
                        self.datas[0].datetime.date(),
                        f'Market Signal: stock {stock_id}, action: {action}, '
                        f'adjust position to {target_short:.2f}')
                    symbol = dt.datetime.now().strftime('%Y-%m-%d')
                    bsu.Utils.write_daily_alert(symbol, stock_id, action)

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                bsu.Utils.log(self.datas[0].datetime.date(),
                              'Stock %s buy Executed, portfolio value is %.2f' %
                              (self.params.ma_periods.get('stock_id'),
                               self.broker.get_value()))
            else:
                bsu.Utils.log(self.datas[0].datetime.date(),
                              'Stock %s sell Executed, portfolio value is %.2f' %
                              (self.params.ma_periods.get('stock_id'),
                               self.broker.get_value()))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.isbuy():
                bsu.Utils.log(self.datas[0].datetime.date(),
                              'Stock %s buy order Canceled/Margin/Rejected, order_status is %d' %
                              (self.params.ma_periods.get('stock_id'),
                               order.status))
            else:
                bsu.Utils.log(self.datas[0].datetime.date(),
                              'Stock %s sell order Canceled/Margin/Rejected, order_status is %d' %
                              (self.params.ma_periods.get('stock_id'),
                               order.status))

        self.order = None