# -*- coding: utf-8 -*-
import datetime as dt
import bdshare as bds
import pandas as pd

import backtraderbd.data.utils as bdu
from backtraderbd.settings import settings as conf
from backtraderbd.libs.log import get_logger
from backtraderbd.libs.models import get_or_create_library


logger = get_logger(__name__)

class DseHisData(object):
    """
    Mapping one collection in 'dse_his_lib' library, download and
    maintain history data from dse using bdshare, and provide other modules with the data.
    columns: open, high, close, low, volume
    Attributes:
        coll_name(string): stock id like 'ACI'.

    """

    def __init__(self, coll_name):
        self._lib_name = conf.BD_STOCK_LIBNAME
        self._coll_name = coll_name
        self._library = get_or_create_library(self._lib_name)
        #self._unused_cols = ['TRADING CODE', 'LTP*', 'YCP', 'TRADE', 'VALUE (mn)']
        self._unused_cols = []
        self._new_added_colls = []

    @classmethod
    def download_one_delta_data(cls, coll_name):
        """
        Download all the collections' delta data.
        :param coll_name: a stock code
        :return: None
        """
        bds_his_data = DseHisData(coll_name)
        bds_his_data.download_delta_data()

    @classmethod
    def download_all_delta_data(cls):
        """
        Download all the collections' delta data.
        :param coll_names: list of the collections.
        :return: None
        """

        bds_his_data = DseHisData(coll_name=None)
        bds_his_data.download_delta_data()

    def download_delta_data(self):
        """
        Get yesterday's data and append it to collection,
        this method is planned to be executed at each day's 8:30am to update the data.
        1. Connect to arctic and get the library.
        2. Get today's history data from bdshare and strip the unused columns.
        3. Store the data to arctic.
        :return: None
        """

        self._init_coll()

        if self._coll_name in self._new_added_colls:
            return

        # 15:00 PM can get today data
        # start = latest_date + 1 day
        latest_date = self.get_data().index[-1]
        start = latest_date + dt.timedelta(days=1)
        start = dt.datetime.strftime(start, '%Y-%m-%d')

        his_data = bds.get_basic_hist_data(
            start=start,
            end=start,
            code=self._coll_name
        )

        # delta data is empty
        if len(his_data) == 0:
            logger.info(
                f'delta data of stock {self._coll_name} is empty, after {start}')
            return

        his_data = bdu.Utils.strip_unused_cols(his_data, *self._unused_cols)

        logger.info(f'got delta data of stock: {self._coll_name}, after {start}')
        self._library.append(self._coll_name, his_data)

    def get_data(self):
        """
        Get all the data of one collection.
        :return: data(DataFrame)
        """

        data = self._library.read(self._coll_name).data
        # parse the date
        data.index = data.index.map(bdu.Utils.parse_date)

        return data

    def _init_coll(self):
        """
        Get all the history data when initiate the library.
        1. Connect to arctic and create the library.
        2. Get all the history data from tushare and strip the unused columns.
        3. Store the data to arctic.
        :return: None
        """

        # if collection is not initialized
        if self._coll_name not in self._library.list_symbols():
            self._new_added_colls.append(self._coll_name)
            #end = dt.datetime.now().strftime('%Y-%m-%d')
            end = dt.datetime.now().date()
            #start = end - dt.timedelta(days=2*360)
            his_data = bds.get_basic_hist_data('2008-01-01', end, code=self._coll_name, index='date').sort_index()
            if len(his_data) == 0:
                logger.warning(
                    f'data of stock {self._coll_name} when initiation is empty'
                )
                return

            #his_data = bdu.Utils.strip_unused_cols(his_data, *self._unused_cols)

            logger.debug(f'write history data for stock: {self._coll_name}.')
            self._library.write(self._coll_name, his_data)
