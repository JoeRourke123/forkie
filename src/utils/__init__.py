import json


def result(type, args={}):
    returnDict = {
        "result": type
    }
    returnDict.update(args)

    return json.dumps(returnDict)
