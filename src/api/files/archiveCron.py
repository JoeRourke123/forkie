from datetime import datetime, timedelta
from traceback import print_exc
from app import app
from src.api.files.utils import getFileVersions, setVersionArchive
from src.db.FileTable import FileTable
from src.db import db

def checkFiles():
    try:
        yearAgo = datetime.now() - timedelta(days=365)
        count = 0
        allFiles = FileTable.query.all()

        for file in allFiles:
            versions = getFileVersions(str(file.fileid))

            if versions[0]["uploaded"] > yearAgo:
                count += 1
                for version in versions:
                    setVersionArchive(version["versionid"], True)

        print(str(count) + " files have been archived...")
        return True
    except Exception as e:
        print(print_exc())
        return False


if __name__ == "__main__":
    checkFiles()