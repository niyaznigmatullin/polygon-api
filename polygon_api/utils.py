from .exceptions import WrongScheme


def convert_to_bytes(x):
    if isinstance(x, bytes):
        return x
    return bytes(str(x), 'utf8')


class DictObj(object):
    def __init__(self, data, required):
        self.__dict__ = data
        for x in required:
            if x not in data:
                raise WrongScheme("parameter '%s' is required" % x)
