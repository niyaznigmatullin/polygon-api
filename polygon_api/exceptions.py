class ProblemNotFoundError(Exception):
    pass


class PolygonApiError(Exception):
    def __init__(self, comment):
        self.comment = comment


class HttpError(Exception):
    def __init__(self, code):
        self.code = code


class WrongScheme(Exception):
    def __init__(self, comment):
        self.comment = comment


class WrongArguments(Exception):
    def __init__(self, comment):
        self.comment = comment