import os
import sys

import datetime as dt
import math

import backtrader as bt

import backtraderbd.data.bdshare as bds
import backtraderbd.strategies.utils as bsu
from backtraderbd.settings import settings as conf
from backtraderbd.libs.log import get_logger
from backtraderbd.libs.models import get_or_create_library

logger = get_logger(__name__)


class BaseStrategy(bt.Strategy):
    """
    Base Strategy template for all strategies to be added to fastquant
    """

    # Strategy level arguments
    # After initialization, the `params` variable becomes accessible as an attribute of the strategy object
    # with the properties of a `named tuple`
    params = (
        ("init_cash", conf.INIT_CASH),
        ("buy_prop", conf.BUY_PROP),
        ("sell_prop", conf.SELL_PROP),
        (
            "execution_type",
            "close",
        ),  # Either open or close, to indicate if a purchase is executed based on the next open or close
        ("periodic_logging", False),
        ("transaction_logging", True),
    )

    def __init__(self):
        # Global variables
        self.init_cash = self.params.init_cash
        self.buy_prop = self.params.buy_prop
        self.sell_prop = self.params.sell_prop
        self.execution_type = self.params.execution_type
        self.periodic_logging = self.params.periodic_logging
        self.transaction_logging = self.params.transaction_logging
        print("===Global level arguments===")
        print("init_cash : {}".format(self.init_cash))
        print("buy_prop : {}".format(self.buy_prop))
        print("sell_prop : {}".format(self.sell_prop))

        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Number of ticks in the input data
        self.len_data = len(list(self.datas[0]))

    def buy_signal(self):
        stock_id = self.params.ma_periods.get('stock_id')
        action = 'buy'
        bsu.Utils.log(
            self.datas[0].datetime.date(),
            f'Market Signal: stock {stock_id}, action: {action}, '
            f'adjust position to {target_long:.2f}')
        symbol = dt.datetime.now().strftime('%Y-%m-%d')
        bsu.Utils.write_daily_alert(symbol, stock_id, action)
        return True

    def sell_signal(self):
        stock_id = self.params.ma_periods.get('stock_id')
        action = 'sell'
        bsu.Utils.log(
            self.datas[0].datetime.date(),
            f'Market Signal: stock {stock_id}, action: {action}, '
            f'adjust position to {target_short:.2f}')
        symbol = dt.datetime.now().strftime('%Y-%m-%d')
        bsu.Utils.write_daily_alert(symbol, stock_id, action)
        return True

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                bsu.Utils.log(self.datas[0].datetime.date(),
                              'Stock %s buy Executed, portfolio value is %.2f' %
                              (self.params.ma_periods.get('stock_id'),
                               self.broker.get_value()))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                if self.transaction_logging:
                    self.log(
                        "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                        % (
                            order.executed.price,
                            order.executed.value,
                            order.executed.comm,
                        )
                    )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if self.transaction_logging:
                if not self.periodic_logging:
                    self.log("Cash %s Value %s" % (self.cash, self.value))
                self.log("Order Canceled/Margin/Rejected")
                self.log("Canceled: {}".format(order.status == order.Canceled))
                self.log("Margin: {}".format(order.status == order.Margin))
                self.log("Rejected: {}".format(order.status == order.Rejected))

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        if self.transaction_logging:
            self.log(
                "OPERATION PROFIT, GROSS %.2f, NET %.2f"
                % (trade.pnl, trade.pnlcomm)
            )

    def notify_cashvalue(self, cash, value):
        # Update cash and value every period
        if self.periodic_logging:
            self.log("Cash %s Value %s" % (cash, value))
        self.cash = cash
        self.value = value

    def next(self):
        if self.periodic_logging:
            self.log("Close, %.2f" % self.dataclose[0])
        if self.order:
            return

        # Skip the last observation since purchases are based on next day closing prices (no value for the last observation)
        if len(self) + 1 >= self.len_data:
            return

        if self.periodic_logging:
            self.log("CURRENT POSITION SIZE: {}".format(self.position.size))
        # Only buy if there is enough cash for at least one stock
        if self.cash >= self.dataclose[0]:
            if self.buy_signal():

                if self.transaction_logging:
                    self.log("BUY CREATE, %.2f" % self.dataclose[0])
                # Take a 10% long position every time it's a buy signal (or whatever is afforded by the current cash position)
                # "size" refers to the number of stocks to purchase
                # Afforded size is based on closing price for the current trading day
                # Margin is required for buy commission
                # Add allowance to commission per transaction (avoid margin)
                afforded_size = int(
                    self.cash
                    / (
                        self.dataclose[0]
                        * (1 + COMMISSION_PER_TRANSACTION + 0.001)
                    )
                )
                buy_prop_size = int(afforded_size * self.buy_prop)
                # Buy based on the closing price of the next closing day
                if self.execution_type == "close":
                    final_size = min(buy_prop_size, afforded_size)
                    if self.transaction_logging:
                        self.log("Cash: {}".format(self.cash))
                        self.log("Price: {}".format(self.dataclose[0]))
                        self.log("Buy prop size: {}".format(buy_prop_size))
                        self.log("Afforded size: {}".format(afforded_size))
                        self.log("Final size: {}".format(final_size))
                    # Explicitly setting exectype=bt.Order.Close will make the next day's closing the reference price
                    self.order = self.buy(size=final_size)
                # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
                else:
                    # Margin is required for buy commission
                    afforded_size = int(
                        self.cash
                        / (
                            self.dataopen[1]
                            * (1 + COMMISSION_PER_TRANSACTION + 0.001)
                        )
                    )
                    final_size = min(buy_prop_size, afforded_size)
                    if self.transaction_logging:
                        self.log("Buy prop size: {}".format(buy_prop_size))
                        self.log("Afforded size: {}".format(afforded_size))
                        self.log("Final size: {}".format(final_size))
                    self.order = self.buy(size=final_size)

        # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
        stock_value = self.value - self.cash
        if stock_value > 0:
            if self.sell_signal():
                if self.transaction_logging:
                    self.log("SELL CREATE, %.2f" % self.dataclose[1])
                # Sell a 5% sell position (or whatever is afforded by the current stock holding)
                # "size" refers to the number of stocks to purchase
                if self.execution_type == "close":
                    if SELL_PROP == 1:
                        self.order = self.sell(
                            size=self.position.size, exectype=bt.Order.Close
                        )
                    else:
                        # Sell based on the closing price of the next closing day
                        self.order = self.sell(
                            size=int(
                                (stock_value / (self.dataclose[1]))
                                * self.sell_prop
                            ),
                            exectype=bt.Order.Close,
                        )
                else:
                    # Sell based on the opening price of the next closing day (only works "open" data exists in the dataset)
                    self.order = self.sell(
                        size=int(
                            (self.init_cash / self.dataopen[1])
                            * self.sell_prop
                        )
                    )

    @classmethod
    def get_data(cls, coll_name):
        """
        Get the time serials used by strategy.
        :param coll_name: stock id (string).
        :return: time serials(DataFrame).
        """
        dse_his_data = bds.DseHisData(coll_name)

        return dse_his_data.get_data()

    @classmethod
    def get_all_data(cls, coll_name=None):
        """
        Get the time serials used by strategy.
        :param coll_name: stock id (string).
        :return: time serials(DataFrame).
        """
        dse_his_data = bds.DseHisData(coll_name)

        return dse_his_data.get_data()

    @classmethod
    def get_params_list(cls, training_data, stock_id):
        """
        Get the params list for finding the best strategy.
        :param training_data(DateFrame): data for training.
        :param stock_id(integer): stock on which strategy works.
        :return: list(dict)
        """
        params_list = []

        data_len = len(training_data)
        ma_l_len = math.floor(data_len * 0.2)
        # data_len = 10

        # ma_s_len is [1, data_len * 0.1)
        ma_s_len = math.floor(data_len * 0.1)

        for i in range(1, int(ma_s_len)):
            for j in range(i + 1, int(ma_l_len), 5):
                params = dict(
                    ma_period_s=i,
                    ma_period_l=j,
                    stock_id=stock_id
                )
                params_list.append(params)

        return params_list

    @classmethod
    def train_strategy(cls, training_data, stock_id):
        """
        Find the optimized parameter of the stategy by using training data.
        :param training_data(DataFrame): data used to train the strategy.
        :param stock_id(integer): stock on which the strategy works.
        :return: params(dict like {ma_periods: dict{ma_period_s: 1, ma_period_l: 2, stock_id: '0'}}
        """
        # get the params list
        params_list = cls.get_params_list(training_data, stock_id)

        al_results = []

        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=training_data)

        cerebro.adddata(data)
        cerebro.optstrategy(cls, ma_periods=params_list)
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='al_return',
                            timeframe=bt.analyzers.TimeFrame.NoTimeFrame)
        cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='al_max_drawdown')

        cerebro.broker.setcash(conf.DEFAULT_CASH)

        logger.debug(f'Starting train the strategy for stock {stock_id}...')

        results = cerebro.run()

        for result in results:
            params = result[0].params
            analyzers = result[0].analyzers
            al_return_rate = analyzers.al_return.get_analysis()
            total_return_rate = 0.0
            for k, v in al_return_rate.items():
                total_return_rate = v
            al_result = dict(
                params=params,
                total_return_rate=total_return_rate,
                max_drawdown=analyzers.al_max_drawdown.get_analysis().get('maxdrawdown'),
                max_drawdown_period=analyzers.al_max_drawdown.get_analysis().get('maxdrawdownperiod')
            )
            al_results.append(al_result)

        # Get the best params
        best_al_result = bsu.Utils.get_best_params(al_results)

        params = best_al_result.get('params')
        ma_periods = params.ma_periods

        logger.debug(
            'Stock %s best parma is ma_period_s: %d, ma_period_l: %d' %
            (
                ma_periods.get('stock_id'),
                ma_periods.get('ma_period_s'),
                ma_periods.get('ma_period_l')
            ))

        return params

    @classmethod
    def run_training(cls, stock_id):
        # get the data
        data = cls.get_data(stock_id)

        # train the strategy for this stock_id to get the params
        params = cls.train_strategy(data, stock_id)

        return params

    @classmethod
    def run_back_testing(cls, stock_id):
        """
        Run the back testing, return the analysis data.
        :param stock_id(string)
        :return(dict): analysis data.
        """
        # get the data
        data = cls.get_data(stock_id)
        length = len(data)
        # get the params
        best_params = cls.get_params(stock_id)

        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=data)

        cerebro.adddata(data)
        ma_periods = best_params.ma_periods
        cerebro.addstrategy(cls, ma_periods=dict(ma_period_s=ma_periods.get('ma_period_s'),
                                                 ma_period_l=ma_periods.get('ma_period_l'),
                                                 stock_id=ma_periods.get('stock_id')))
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='al_return',
                            timeframe=bt.analyzers.TimeFrame.NoTimeFrame)

        cerebro.addanalyzer(bad.TimeDrawDown, _name='al_max_drawdown')

        cerebro.broker.set_cash(bsu.Utils.DEFAULT_CASH)

        logger.debug(
            'Starting back testing, stock is %s, params is ma_period_s: %d, ma_period_l: %d...' %
            (
                ma_periods.get('stock_id'),
                ma_periods.get('ma_period_s'),
                ma_periods.get('ma_period_l')
            ))

        strats = cerebro.run()
        strat = strats[0]

        for k, v in strat.analyzers.al_return.get_analysis().items():
            total_return_rate = v

        al_result = dict(
            stock_id=ma_periods.get('stock_id'),
            trading_days=length,
            total_return_rate=total_return_rate,
            max_drawdown=strat.analyzers.al_max_drawdown.get_analysis().get('maxdrawdown'),
            max_drawdown_period=strat.analyzers.al_max_drawdown.get_analysis().get('maxdrawdownperiod'),
            drawdown_points=strat.analyzers.al_max_drawdown.get_analysis().get('drawdownpoints')
        )

        # cerebro.plot()

        return al_result

    @classmethod
    def get_params(cls, stock_id):
        """
        Get the params of the stock_id for this strategy.
        :param stockid:
        :return: dict(like dict(ma_periods=dict(ma_period_s=0, ma_period_l=0, stock_id='0')))
        """
        lib = get_or_create_library(conf.STRATEGY_PARAMS_LIBNAME)
        symbol = cls.name

        params_list = lib.read(symbol).data
        params = params_list.loc[stock_id, 'params']

        return params

    @classmethod
    def is_stock_in_symbol(cls, stock_id, symbol, lib):
        params_list = lib.read(symbol).data

        if stock_id in params_list.index:
            return True
        else:
            return False
