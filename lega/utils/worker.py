
from functools import partial
from ..utils import db


class Worker(object):
    def __init__(self):
        pass

    def worker(self, *args, **kwargs):
        # TODO Do error logging in THIS function instead of wrapping it like this
        func = db.catch_error(db.crypt4gh_to_user_errors(self.do_work))
        return partial(func, *args, **kwargs)
