""" General utils for files API
"""
import os
from datetime import datetime

from sqlalchemy import and_

from src.api.files.backblaze import B2Interface
from src.api.user.utils import getUserData

from src.db import db
from src.db.FileVersionTable import FileVersionTable
from src.db.GroupTable import GroupTable
from src.db.FileGroupTable import FileGroupTable
from src.db.MetadataTable import MetadataTable

from src.api.files.backblaze import application_key
from src.api.files.backblaze import application_key_id
from src.api.files.backblaze import file_rep_bucket


def getFileExtension(filename: str) -> str:
    return os.path.splitext(filename)[1]


def getFileVersions(fileID):
    versions = list(FileVersionTable.query.filter(FileVersionTable.fileid == fileID).all())
    results = []

    for version in versions:
        metadata = MetadataTable.query.filter(MetadataTable.versionid == version.versionid).all()

        versionData = {
            "versionid": version.versionid,
            "versionhash": version.versionhash,
        }

        for data in metadata:
            if data.title == "userid":
                versionData["author"] = getUserData(data.value)
            # elif data.title == "uploaded":
            #     versionData["uploaded"] = datetime.fromisoformat(data.value)
            else:
                versionData[data.title] = data.value

        results.append(versionData)

    return sorted(results, key=lambda x: x["uploaded"], reverse=True)


def getFileGroups(fileID):
    return GroupTable.query.join(FileGroupTable, and_(GroupTable.groupid == FileGroupTable.groupid, FileGroupTable.fileid == fileID)).all()


def newFileVersion(fileData, uploadData, userid):
    b2 = B2Interface(application_key_id, application_key, file_rep_bucket)

    fileversion = FileVersionTable({
        "fileid": fileData.fileid,
        "versionhash": "temp"
    })

    upload = b2.uploadFile(data=uploadData.read(),
                  versionid=fileversion.versionid,
                  filename=uploadData.filename,
                  fileid=str(fileData.fileid),
                  extension=fileData.extension)

    fileversion.versionhash = upload.get_content_sha1()

    db.session.add(fileversion)
    db.session.commit()

    userMetadata = MetadataTable({
        "versionid": fileversion.versionid,
        "title": "userid",
        "value": userid
    })
    timeMetadata = MetadataTable({
        "versionid": fileversion.versionid,
        "title": "uploaded",
        "value": str(datetime.now())
    })

    db.session.add(userMetadata)
    db.session.add(timeMetadata)
    db.session.commit()

    return "File Uploaded"