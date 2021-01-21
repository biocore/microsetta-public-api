import logging
from functools import wraps
from time import time

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s ')
logger = logging.getLogger(__name__)


class timeit:

    def __init__(self, msg):
        self.msg = msg

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time()
            result = f(*args, **kwargs)
            end = time()
            total = end - start
            logger.info('%(message)s Elapsed: %(elapsed)s',
                        {'message': self.msg, 'elapsed': total})
            return result
        return wrapper
