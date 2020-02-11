from src.db.MetadataTable import MetadataTable

from traceback import print_exc

def getMetadata(versionID):
    try:
        res = MetadataTable.query.filter(versionid = versionID)
        return res

    except Exception as e:
        return print_exc()
