from __future__ import (absolute_import, division, print_function, unicode_literals)
import os
import sys

import datetime as dt
import math
import pandas as pd

import backtrader as bt

import backtraderbd.data.bdshare as bds
import backtraderbd.strategies.utils as bsu
from backtraderbd.settings import settings as conf
from backtraderbd.libs.log import get_logger
from backtraderbd.libs.models import get_or_create_library

from backtraderbd.strategies.rsi import RSIStrategy
from backtraderbd.strategies.emac import EMACStrategy
from backtraderbd.strategies.macd import MACDStrategy
from backtraderbd.strategies.smac import SMACStrategy

logger = get_logger(__name__)


class Btask(object):
    """
    Base Methods
    """
    def __init__(self):
        pass

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
        
        # Change Data Type [https://www.backtrader.com/docu/dataautoref/#pandasdata]
        #convert_dict = {'date': complex, 'high': float, 'low': float, 'close': float, 'volume': int}
        #data = data.astype(convert_dict)
        training_data = training_data.apply(pd.to_numeric)
        training_data.head()

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
    def run_back_testing(cls, strategy, stock_id):
        """
        Run the back testing, return the analysis data.
        :param Strategy(string)
        :param stock_id(string)
        :return(dict): analysis data.
        """
        STRATEGY_MAPPING = {
            "rsi": RSIStrategy,
            "smac": SMACStrategy,
            "macd": MACDStrategy,
            "emac": EMACStrategy,
        }

        # get the data
        data = cls.get_data(stock_id)
        length = len(data)

        print('Data length: {0}'.format(length))

        # Change Data Type [https://www.backtrader.com/docu/dataautoref/#pandasdata]
        #convert_dict = {'date': complex, 'high': float, 'low': float, 'close': float, 'volume': int}
        #data = data.astype(convert_dict)
        data = data.apply(pd.to_numeric)

        # get the params

        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=data)

        cerebro.adddata(data)
        cerebro.addstrategy(STRATEGY_MAPPING[strategy])

        cerebro.broker.setcommission(commission=conf.COMMISSION_PER_TRANSACTION)

        cerebro.broker.setcash(conf.DEFAULT_CASH)

        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        cerebro.run()
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

        cerebro.plot(figsize=(30, 15))

        return True

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
