from datetime import datetime, timedelta
from traceback import print_exc

from src.api.files import filesBP
from src.api.files.utils import getFileVersions, setVersionArchive

from src.db.FileTable import FileTable


@filesBP.route("/archiveCheck")
def checkFiles():
    try:
        yearAgo = datetime.now() - timedelta(days=365)
        count = 0
        allFiles = FileTable.query.all()

        for file in allFiles:
            versions = getFileVersions(str(file.fileid))

            if len(versions) >= 1:
                mostRecent = sorted(versions.keys(), key=lambda vID: versions[vID]["uploaded"], reverse=True)[0]
                # 2020-03-01 22:09:14.935694
                if datetime.strptime(versions[mostRecent]["uploaded"], "%Y-%m-%d %H:%M:%S.%f") < yearAgo:
                    count += 1
                    for version in versions.values():
                        setVersionArchive(version["versionid"], True)

        print(str(count) + " files have been archived...")
        return "Complete"
    except Exception as e:
        print(print_exc())
        return "Not Complete"