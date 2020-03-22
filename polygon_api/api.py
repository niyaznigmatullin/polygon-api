import time
from .utils import convert_to_bytes, DictObj
import random
import hashlib
import json
from .exceptions import *
import requests
from enum import Enum, auto


class PolygonAPI:
    def __init__(self, polygon_url, key, secret, pin=None):
        self.pin = pin
        self.polygon_address = polygon_url
        self.api_key = key
        self.api_secret = secret
        self.session = requests.session()

    def send_api_request(self, api_method, params, is_json=True):
        params["apiKey"] = self.api_key
        params["time"] = int(time.time())
        if self.pin is not None:
            params["pin"] = self.pin
        signature_random = ''.join([chr(random.SystemRandom().randint(0, 25) + ord('a')) for _ in range(6)])
        signature_random = convert_to_bytes(signature_random)
        param_list = []
        for k in params:
            if isinstance(params[k], list):
                for v in params[k]:
                    param_list.append((k, convert_to_bytes(v)))
            else:
                param_list.append((k, convert_to_bytes(params[k])))
        # for k in params:
        #     params[k] = convert_to_bytes(params[k])
        # param_list = [(convert_to_bytes(key), params[key]) for key in params]
        param_list.sort()
        signature_string = signature_random + b'/' + convert_to_bytes(api_method)
        signature_string += b'?' + b'&'.join([convert_to_bytes(i[0]) + b'=' + i[1] for i in param_list])
        signature_string += b'#' + convert_to_bytes(self.api_secret)
        # params["apiSig"] = signature_random + convert_to_bytes(hashlib.sha512(signature_string).hexdigest())
        param_list.append(("apiSig", signature_random + convert_to_bytes(hashlib.sha512(signature_string).hexdigest())))
        url = self.polygon_address + '/api/' + api_method
        print(param_list)
        result = self.session.request('POST', url, files=param_list)
        if result.status_code != 200:
            raise HttpError(result.status_code)
        if not is_json and result.status_code == 200:
            return result.content
        result = json.loads(result.content.decode('utf8'))
        if result["status"] == "FAILED":
            raise PolygonApiError(result["comment"])
        if "result" in result:
            return result["result"]
        return None

    def problems_list(self):
        return list(map(lambda x: Problem(self, x), self.send_api_request("problems.list", {}, True)))


class PointsPolicy(Enum):
    COMPLETE_GROUP = auto()
    EACH_TEST = auto()

    def __str__(self):
        return self.name


class FeedbackPolicy(Enum):
    NONE = auto()
    POINTS = auto()
    ICPC = auto()
    COMPLETE = auto()

    def __str__(self):
        return self.name


class SolutionTag(Enum):
    MA = auto()  # Main correct solution
    OK = auto()  # Accepted
    RJ = auto()  # Rejected, Incorrect
    TL = auto()  # Time limit exceeded
    TO = auto()  # Time limit exceeded or accepted
    WA = auto()  # Wrong answer
    PE = auto()  # Presentation error
    ML = auto()  # Memory limit exceeded
    RE = auto()  # Runtime error

    def __str__(self):
        return self.name


class FileType(Enum):
    RESOURCE = auto()
    SOURCE = auto()
    AUX = auto()

    def __str__(self):
        return self.name


class Problem(DictObj):
    id = None
    owner = None
    name = None
    deleted = None
    favourite = None
    accessType = None
    revision = None
    modified = None
    latestPackage = None

    def __init__(self, api, data):
        super().__init__(data, ["id", "owner", "name", "deleted", "favourite", "accessType", "revision", "modified"])
        self.api = api

    def send_api_request(self, api_method, params, is_json=True):
        params["problemId"] = self.id
        return self.api.send_api_request(api_method, params, is_json=is_json)

    def extractParams(self, params, required_params=None):
        res = {x: y for x, y in params.items() if x != 'self' and y is not None}
        if required_params is not None:
            for x in required_params:
                if x not in params:
                    raise WrongArguments("%s should be defined")
        for x in res:
            if isinstance(res[x], bool):
                res[x] = 'true' if res[x] else 'false'
        return res

    def info(self):
        return ProblemInfo(self.api, self.send_api_request("problem.info", {}))

    def updateInfo(self, inputFile=None, outputFile=None, interactive=None, timeLimit=None, memoryLimit=None):
        params = self.extractParams(locals())
        return self.send_api_request("problem.updateInfo", params)

    def saveTest(self, testset, testIndex, testInput, testGroup=None, testPoints=None, testDescription=None,
                 testUseInStatements=None, testInputForStatements=None, testOutputForStatements=None,
                 verifyInputOutputForStatements=None, checkExisting=None):
        params = self.extractParams(locals(), ['testset', 'testIndex', 'testInput'])
        return self.send_api_request("problem.saveTest", params)

    def setTestGroup(self, testset, testGroup, testIndex):
        params = self.extractParams(locals(), ['testset', 'testGroup', 'testIndex'])
        return self.send_api_request("problem.setTestGroup", params)

    def enableGroups(self, testset, enable):
        params = self.extractParams(locals(), ['testset', 'enable'])
        return self.send_api_request("problem.enableGroups", params)

    def enablePoints(self, enable):
        params = self.extractParams(locals(), ['enable'])
        return self.send_api_request("problem.enablePoints", params)

    def saveTestGroup(self, testset, group, pointsPolicy=None, feedbackPolicy=None, dependencies=None):
        """

        :param testset: String
        :param group: Integer or String
        :param pointsPolicy: PointsPolicy
        :param feedbackPolicy: FeedbackPolicy
        :param dependencies: List[String|Integer] or String or Integer
        :return:
        """
        if isinstance(dependencies, list):
            dependencies = ",".join(map(str, dependencies))
        else:
            dependencies = str(dependencies)
        if not isinstance(pointsPolicy, PointsPolicy):
            raise ValueError(
                "Expected PointsPolicy instance for pointsPolicy argument, but %s found" % type(pointsPolicy))
        if not isinstance(feedbackPolicy, FeedbackPolicy):
            raise ValueError(
                "Expected FeedbackPolicy instance for feedbackPolicy argument, but %s found" % type(feedbackPolicy))
        params = self.extractParams(locals(), ['testset', 'group'])
        return self.send_api_request("problem.saveTestGroup", params)

    def checker(self):
        return self.send_api_request("problem.checker", {})

    def validator(self):
        return self.send_api_request("problem.validator", {})

    def interactor(self):
        return self.send_api_request("problem.interactor", {})

    def files(self):
        d = self.send_api_request("problem.files", {})
        for t in d:
            d[t] = File(self.api, d[t])
        return d

    def saveSolution(self, name, file, sourceType, tag, checkExisting=None):
        params = self.extractParams(locals(), ['name', 'file', 'sourceType', 'tag'])
        return self.send_api_request("problem.saveSolution", params)

    def saveFile(self, type, name, file, sourceType=None):  # TODO add forTypes, stages, assets
        params = self.extractParams(locals(), ['type', 'name', 'file'])
        return self.send_api_request("problem.saveFile", params)


class ProblemInfo(DictObj):
    inputFile = None
    outputFile = None
    interactive = None
    timeLimit = None
    memoryLimit = None

    def __init__(self, api, data):
        super().__init__(data, self.__dict__.keys())
        self.api = api


class File(DictObj):
    name = None
    modificationTimeSeconds = None
    length = None
    sourceType = None
    resourceAdvancedProperties = None
    
    def __init__(self, api, data):
        super().__init__(data, ['name', 'modificationTimeSeconds', 'length'])
        self.api = api
