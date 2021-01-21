import logging
from functools import wraps
from time import time
import os

FORMAT = '%(asctime)s PID={pid} %(levelname)s: %(message)s '
logging.basicConfig(level=logging.INFO,
                    format=FORMAT.format(pid=os.getpid()))
logger = logging.getLogger(__name__)


class timeit:

    def __init__(self, msg):
        self.msg = msg

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger.info('%(message)s Start.',
                        {'message': self.msg},
                        )
            start = time()
            result = f(*args, **kwargs)
            end = time()
            total = end - start
            logger.info('%(message)s Elapsed: %(elapsed)s',
                        {'message': self.msg, 'elapsed': total},
                        )
            return result
        return wrapper
