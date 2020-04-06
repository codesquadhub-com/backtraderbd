from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()

setup_args = dict(
    name='backtraderbd',
    version='0.0.1',
    description='A backtrader utility',
    long_description_content_type="text/markdown",
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    packages=find_packages(),
    author='Raisul Islam',
    author_email='raisul.exe@gmail.com',
    keywords=['backtrader','backtester'],
    url='https://github.com/rochi88/backtraderbd',
    download_url='https://pypi.org/project/elastictools/'
)

install_requires = [
    'beautifulsoup4',	# tushare require
    'lxml', # tushare require
    'xlrd', # tushare require
    'requests', # tushae require
    'pandas==0.20.1',
    'backtrader',
    'tushare',
    'arctic',
    'WeRoBot==1.1.1',
    'gevent',
    'easytrader==0.12.3',
    'demjson==2.2.4',
    'retrying==1.3.3'
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)