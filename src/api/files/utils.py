""" General utils for files API
"""
import os
from datetime import datetime
from traceback import print_exc

from sqlalchemy import and_

from src.api.email.utils import sendGroupEmail
from src.api.files.backblaze import B2Interface
from src.api.user.utils import getUserData

from src.db import db
from src.db.FileVersionTable import FileVersionTable
from src.db.GroupTable import GroupTable
from src.db.FileGroupTable import FileGroupTable
from src.db.MetadataTable import MetadataTable


def getFileExtension(filename: str) -> str:
    return os.path.splitext(filename)[1]


def getFileVersions(fileID):
    try:
        versions = list(FileVersionTable.query.filter(FileVersionTable.fileid == fileID).all())
        results = []

        for version in versions:
            metadata = MetadataTable.query.filter(MetadataTable.versionid == version.versionid).all()

            versionData = {
                "versionid": str(version.versionid),
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
    except Exception as e:
        print(print_exc())

        return []

def getFileGroups(fileID):
    return [group.serialise() for group in GroupTable.query.join(FileGroupTable, and_(GroupTable.groupid == FileGroupTable.groupid, FileGroupTable.fileid == fileID)).all()]


def newFileVersion(fileData, uploadData, title, userid):
    b2 = B2Interface(
        os.environ.get("APPLICATION_KEY_ID"),
        os.environ.get("APPLICATION_KEY"),
        os.environ.get("BUCKET_NAME")
    )

    fileversion = FileVersionTable({
        "fileid": fileData["fileid"],
        "versionhash": "temp"
    })

    upload = b2.uploadFile(data=uploadData.read(),
                           versionid=fileversion.versionid,
                           filename=fileData["filename"],
                           fileid=str(fileData["fileid"]),
                           extension=fileData["extension"])

    if not b2.checkForEqualFiles(upload.get_content_sha1(),
                                 filename=fileData["filename"],
                                 size=upload.get_content_length(),
                                 versions=getFileVersions(str(fileData["fileid"]))):
        return False

    fileversion.versionhash = upload.get_content_sha1()

    db.session.add(fileversion)
    db.session.commit()

    authorData = MetadataTable({
        "versionid": fileversion.versionid,
        "title": "userid",
        "value": userid
    })

    uploadData = MetadataTable({
        "versionid": fileversion.versionid,
        "title": "uploaded",
        "value": str(datetime.now())
    })

    titleData = MetadataTable({
        "versionid": fileversion.versionid,
        "title": "title",
        "value": title
    })

    db.session.add(titleData)
    db.session.add(authorData)
    db.session.add(uploadData)
    db.session.commit()

    userData = getUserData(userid)

    for group in getFileGroups(fileData["fileid"]):
        sendGroupEmail(group["groupid"], {
            "subject": "New Version of " + fileData["filename"] + " Created",
            "content": "Hi there!\n" + userData["username"] + " (" + userData["email"] + ") has created a new version of " +
                       fileData["filename"] + " with the title \"" + titleData.value + "\". \n\nThanks,\nfile-rep0"
        }, userData)

    return True


def leaderCheck(groupList, userid):
    return True in [group["groupleaderid"] == userid for group in groupList]