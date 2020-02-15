""" General utils for files API
"""
import os

from src.api.files.backblaze import B2Interface

from src.db import db
from src.db.FileVersionTable import FileVersionTable

from src.api.files.backblaze import application_key
from src.api.files.backblaze import application_key_id
from src.api.files.backblaze import file_rep_bucket


def getFileExtension(filename: str) -> str:
    return os.path.splitext(filename)[1]


def newFileVersion(fileData, uploadData, userData):
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

    return "File Uploaded"