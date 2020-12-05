from pyrae import core
from pyrae import logger
from sys import version_info
from typing import Optional
from urllib.error import URLError, HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def search_by_url(url: str) -> Optional[core.SearchResult]:
    """ Performs a search given the full URL to the RAE.

    :param url: A full URl to the RAE.
    :return: A SearchResult instance, or None if an error occurs.
    """
    if not url:
        logger.current.error('No URL was specified.')
        return None
    if not url.startswith(core.DLE_MAIN_URL):
        logger.current.error(f"The URL '{url}' seems to be invalid, it does not start with the known "
                             f"'{core.DLE_MAIN_URL}' URL.")
        return None
    logger.current.info(f"Performing request to: '{url}'...")
    try:
        with urlopen(Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})) as response:
            status_code = response.status if version_info >= (3, 9, 0) else response.code
            logger.current.debug(f'Received response with OK status code {status_code}.')
            result = core.SearchResult(html=response.read())
            return result
    except HTTPError as e:
        logger.current.error(f'The server could not fulfill the request. Error code: {e.code}.')
        return None
    except URLError as e:
        logger.current.error(f'Failed to reach a server. Reason: {e.reason}')
        return None
    except Exception as e:
        logger.current.error(f'Unexpected error. str{e}')
        return None


def search_by_word(word: str) -> Optional[core.SearchResult]:
    """ Performs a search given a word or search term.

    :param word: A word or term to search for.
    :return: A SearchResult instance, or None if an error occurs.
    """
    if not word:
        logger.current.error('No word was specified.')
        return None
    full_url = f'{core.DLE_MAIN_URL}/{quote(word)}'
    return search_by_url(url=full_url)


def set_log_level(log_level: str):
    """ Sets the log level of the logger.

    :param log_level: The level of logging used:
                        DEBUG:   Detailed information, typically of interest only when diagnosing problems.
                        INFO:    Confirmation that things are working as expected.
                        WARNING: An indication that something unexpected happened, but processing continues.
                        ERROR:   A serious problem that causes processing to stop.
    """
    logger.init_logger(log_level=log_level)


set_log_level(log_level='INFO')
