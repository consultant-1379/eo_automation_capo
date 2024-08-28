import logging
import time
from functools import wraps


def retry(exception_to_check, tries=5, delay=2, backoff=1):
    """
    Decorator which runs function until it succeeds i.e. :param exception_to_check is not thrown
    :param exception_to_check: rerun the function if this exception is thrown
    :param tries: (int) maximum number of attempts
    :param delay: pause (seconds) which is used before each attempt
    :param backoff: (int) coefficient to increase :param delay before any subsequent attempt
    """

    def deco_retry(func):
        @wraps(func)
        def f_retry(*args, **kwargs):
            dec_tries, dec_delay = tries, delay
            while dec_tries > 1:
                try:
                    return func(*args, **kwargs)
                except exception_to_check as exception:
                    try:
                        message = f", exception message is: '{exception.args[0]}'"
                    except IndexError:
                        message = ''
                    dec_tries -= 1
                    logging.debug(
                        f"Happened {exception_to_check}{message}, retrying in {round(dec_delay, 2)} seconds... tries left {dec_tries}")
                    time.sleep(dec_delay)
                    dec_delay *= backoff
            return func(*args, **kwargs)

        return f_retry

    return deco_retry


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance
