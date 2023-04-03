from functools import wraps
from time import time


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        print(f"func:{f.__name__} took: {round(time() - ts, 3)} sec")
        return result

    return wrap
