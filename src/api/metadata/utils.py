from traceback import print_exc

from src.db.MetadataTable import MetadataTable


def getMetadata(versionID):
    try:
        res = MetadataTable.query.filter_by(versionid=versionID)
        return res

    except Exception as e:
        return print_exc()