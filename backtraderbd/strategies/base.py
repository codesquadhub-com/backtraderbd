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

logger = get_logger(__name__)


class BaseStrategy(bt.Strategy):
    """
    Base Strategy template for all strategies to be added
    """
    def __init__(self):
        # Global variables
        self.init_cash = conf.DEFAULT_CASH
        self.buy_prop = conf.BUY_PROP
        self.sell_prop = conf.SELL_PROP
        self.execution_type = conf.EXECUTION_TYPE
        self.periodic_logging = conf.PERIODIC_LOGGING
        self.transaction_logging = conf.TRANSACTION_LOGGING
        print("===Global level arguments===")
        print("init_cash : {}".format(self.init_cash))
        print("buy_prop : {}".format(self.buy_prop))
        print("sell_prop : {}".format(self.sell_prop))
        self.dataclose = self.datas[0].close    # Keep a reference to the "close" line in the data[0] dataseries
        self.dataopen = self.datas[0].open
        self.order = None   # To keep track of pending orders
        self.buyprice = None
        self.buycomm = None
        self.len_data = len(list(self.datas[0]))    # Number of ticks in the input data

    def buy_signal(self):
        return True

    def sell_signal(self):
        return True

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                if self.transaction_logging:
                    bsu.Utils.log(
                        "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                        % (
                            order.executed.price,
                            order.executed.value,
                            order.executed.comm,
                        )
                    )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                if self.transaction_logging:
                    bsu.Utils.log(
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
                    bsu.Utils.log("Cash %s Value %s" % (self.cash, self.value))
                bsu.Utils.log("Order Canceled/Margin/Rejected")
                bsu.Utils.log("Canceled: {}".format(order.status == order.Canceled))
                bsu.Utils.log("Margin: {}".format(order.status == order.Margin))
                bsu.Utils.log("Rejected: {}".format(order.status == order.Rejected))

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        if self.transaction_logging:
            bsu.Utils.log(
                "OPERATION PROFIT, GROSS %.2f, NET %.2f"
                % (trade.pnl, trade.pnlcomm)
            )

    def notify_cashvalue(self, cash, value):
        # Update cash and value every period
        if self.periodic_logging:
            bsu.Utils.log("Cash %s Value %s" % (cash, value))
        self.cash = cash
        self.value = value

    def next(self):
        # Simply log the closing price of the series from the reference
        if self.periodic_logging:
            bsu.Utils.log("Close, %.2f" % self.dataclose[0])
        
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Skip the last observation since purchases are based on next day closing prices (no value for the last observation)
        if len(self) + 1 >= self.len_data:
            return

        if self.periodic_logging:
            bsu.Utils.log("CURRENT POSITION SIZE: {}".format(self.position.size))
        # Only buy if there is enough cash for at least one stock
        if self.cash >= self.dataclose[0]:
            if self.buy_signal():

                if self.transaction_logging:
                    bsu.Utils.log("BUY CREATE, %.2f" % self.dataclose[0])
                # Take a 10% long position every time it's a buy signal (or whatever is afforded by the current cash position)
                # "size" refers to the number of stocks to purchase
                # Afforded size is based on closing price for the current trading day
                # Margin is required for buy commission
                # Add allowance to commission per transaction (avoid margin)
                afforded_size = int(
                    self.cash
                    / (
                        self.dataclose[0]
                        * (1 + conf.COMMISSION_PER_TRANSACTION + 0.001)
                    )
                )
                buy_prop_size = int(afforded_size * self.buy_prop)
                # Buy based on the closing price of the next closing day
                if self.execution_type == "close":
                    final_size = min(buy_prop_size, afforded_size)
                    if self.transaction_logging:
                        bsu.Utils.log("Cash: {}".format(self.cash))
                        bsu.Utils.log("Price: {}".format(self.dataclose[0]))
                        bsu.Utils.log("Buy prop size: {}".format(buy_prop_size))
                        bsu.Utils.log("Afforded size: {}".format(afforded_size))
                        bsu.Utils.log("Final size: {}".format(final_size))
                    # Explicitly setting exectype=bt.Order.Close will make the next day's closing the reference price
                    self.order = self.buy(size=final_size)
                # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
                else:
                    # Margin is required for buy commission
                    afforded_size = int(
                        self.cash
                        / (
                            self.dataopen[1]
                            * (1 + conf.COMMISSION_PER_TRANSACTION + 0.001)
                        )
                    )
                    final_size = min(buy_prop_size, afforded_size)
                    if self.transaction_logging:
                        bsu.Utils.log("Buy prop size: {}".format(buy_prop_size))
                        bsu.Utils.log("Afforded size: {}".format(afforded_size))
                        bsu.Utils.log("Final size: {}".format(final_size))
                    self.order = self.buy(size=final_size)

        # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
        stock_value = self.value - self.cash
        if stock_value > 0:
            if self.sell_signal():
                if self.transaction_logging:
                    bsu.Utils.log("SELL CREATE, %.2f" % self.dataclose[1])
                # Sell a 5% sell position (or whatever is afforded by the current stock holding)
                # "size" refers to the number of stocks to purchase
                if self.execution_type == "close":
                    if conf.SELL_PROP == 1:
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