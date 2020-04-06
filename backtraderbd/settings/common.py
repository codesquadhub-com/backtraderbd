# -*- coding: utf-8 -*-
import os

PROJECT_NAME = 'backtraderbd'

# log setting
LOG_DIR = '/logs/'
LOG_LEVEL = 'DEBUG'

# database setting
MONGO_HOST = 'localhost'
BD_STOCK_LIBNAME = 'ts_his_lib'
DAILY_STOCK_ALERT_LIBNAME = 'daily_stock_alert'
STRATEGY_PARAMS_LIBNAME = 'strategy_params'
STRATEGY_PARAMS_MA_SYMBOL = 'ma_trend'
LZ4_N_PARALLEL=8


# DSE_CONFIG = {
    # "username": os.getenv('WEIBO_USERNAME', '18628391725'),
    # "password": os.getenv('WEIBO_PASSWORD', 'Gupiao888'),
    # "request_headers": {
        # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
        # 'Pragma': 'no-cache',
        # 'Connection': 'keep-alive',
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        # 'Accept-Encoding': 'gzip, deflate',
        # 'Cache-Control': 'no-cache',
        # 'Referer': 'http://jiaoyi.sina.com.cn/jy/index.php',
        # 'Accept-Language': 'zh-CN,zh;q=0.8'
    # },
    # "login_url": "https://login.sina.com.cn/sso/login.php",
# }
