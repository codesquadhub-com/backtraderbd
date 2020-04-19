# -*- coding: utf-8 -*-
import backtraderbd.strategies.ma as bsm
import backtraderbd.tasks as btasks
from backtraderbd.libs.log import get_logger
from backtraderbd.settings import settings as conf
from backtraderbd.libs import models


logger = get_logger(__name__)


def train(stock):
    """
    Run training tasks via multiprocessing and save training params to arctic store.
    :param stock: str, stock code
    :return: None
    """

    task = btasks.Task(bsm.MATrendStrategy, stock)
    params = task.train()
    # write stock params to MongoDB
    symbol = conf.STRATEGY_PARAMS_MA_SYMBOL
    models.save_training_params(symbol, params)


def main(stock_pools):
    """
    Get all stocks and train params for each stock.
    :param stock_pools: list, the stock code list.
    :return: None
    """

    for stock in stock_pools:
        train(stock)


if __name__ == '__main__':
    # create params library if not exist
    models.get_or_create_library(conf.STRATEGY_PARAMS_LIBNAME)

    bd_stocks = models.get_bd_stocks()
    main(bd_stocks)

