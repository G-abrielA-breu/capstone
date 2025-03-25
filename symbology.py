# symbol conversion

import requests
from typing import Callable, Union
from utils.header import header
from utils.logging import logger
import sys
import time

_symbol_map = None


def _requests() -> dict:
    global _symbol_map
    if not _symbol_map:
        time.sleep(1)
        logger.debug('getting symbol map...')
        _symbol_map = requests.get("https://www.sec.gov/files/company_tickers.json", headers=header())
        if _symbol_map.status_code == 429:
            logger.error('Too many requests')
            sys.exit(1)
    return _symbol_map.json().values()


class TickerNotFoundError(BaseException):

    def __init__(self, ticker):
        self.ticker = ticker

    def __repr__(self):
        return f'CIK for ticker [{self.ticker}] not found'


def _load_ticker(f: Callable[[str], str]) -> Callable[[str], str]:
    """
    decorator to load dict keyed by ticker
    :param f:
    :return:
    """
    def _wrapper(ticker: str) -> str:
        if Ticker2.cache is None:
            Ticker2.cache = dict()
            for s in _requests():
                Ticker2.cache[s['ticker']] = {'CIK': str(s['cik_str']), 'name': s['title']}
        return f(ticker)

    return _wrapper


class Ticker2:

    cache = None

    @staticmethod
    @_load_ticker
    def cik(ticker: str) -> str:
        # in SEC symbology, stock classes are represented by dashes instead of dots (BRK-B instead of BRK.B)
        try:
            return Ticker2.cache[ticker.replace('.', '-')]['CIK']
        except KeyError:
            raise TickerNotFoundError(ticker)

    @staticmethod
    @_load_ticker
    def name(ticker: str) -> str:
        try:
            return Ticker2.cache[ticker]['name']
        except KeyError:
            raise TickerNotFoundError(ticker)

    @staticmethod
    @_load_ticker
    def exists(ticker: str) -> bool:
        return ticker in Ticker2.cache


class CIKNotFoundError(BaseException):

    def __init__(self, ticker):
        self.ticker = ticker

    def __repr__(self):
        return f'CIK for ticker [{self.ticker}] not found'


def _load_cik(f: Callable[[Union[str, int]], Union[str, int]]) -> Callable[[Union[str, int]], Union[str, int]]:
    """
    decorator to load dict keyed by CIK
    :param f:
    :return:
    """

    def _wrapper(cik: Union[str, int]) -> Union[str, int]:
        if CIK2.cache is None:
            CIK2.cache = dict()
            for s in _requests():
                CIK2.cache[str(s['cik_str'])] = {'ticker': str(s['ticker']), 'name': s['title']}
        return f(cik)

    return _wrapper


class CIK2:

    cache = None

    @staticmethod
    @_load_cik
    def ticker(cik: Union[str, int]) -> str:
        try:
            return CIK2.cache[cik]['ticker']
        except KeyError:
            raise CIKNotFoundError(cik)

    @staticmethod
    @_load_cik
    def name(cik: str) -> str:
        try:
            return CIK2.cache[cik]['name']
        except KeyError:
            raise CIKNotFoundError(cik)

    @staticmethod
    @_load_ticker
    def exists(cik: str) -> bool:
        return cik in CIK2.cache


if __name__ == '__main__':
    x = [Ticker2.cik('AAPL'), Ticker2.name('AAPL'), CIK2.ticker('320193'), CIK2.name('320193')]
    pass
