# -*- coding: utf-8 -*-
from backtraderbd.btask import Btask


class Task(object):
    """
    Task for each stock's back testing.
    Attributes:
        Strategy(Strategy): class of strategy used for back testing.
        stock_id(string): id of stock to be back tested.
    """

    def __init__(self, strategy, stock_id):
        self._Strategy = strategy
        self._stock_id = stock_id

    def task(self):
        """
        Task for each stock's back testing.
        1. Execute the back testing.
        2. Get the analysis data of the back testing(average annual return rate,
           max draw down, draw down length, average annual draw down).
        :return: analysis of this back testing(dict).
        """

        # Run back testing, get the analysis data
        # result = self._Strategy.run_back_testing(data, best_param)

        #result = self._Strategy.run_back_testing(self._stock_id)
        result = Btask.run_back_testing(self._Strategy, self._stock_id)

        return result

    def train(self):
        return Btask.run_training(self._stock_id)
