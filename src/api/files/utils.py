""" General utils for files API
"""
import os
from datetime import datetime
from traceback import print_exc

from sqlalchemy import and_

from src.api.email.utils import sendGroupEmail
from src.api.files.backblaze import B2Interface
from src.api.metadata.utils import getMetadata
from src.api.user.utils import getUserData

from src.db import db
from src.db.FileVersionTable import FileVersionTable
from src.db.GroupTable import GroupTable
from src.db.FileGroupTable import FileGroupTable
from src.db.MetadataTable import MetadataTable


def getFileExtension(filename: str) -> str:
    """ Utility function which given a filename will return the file's extension, using the os.path method splittext and
        python's list indexing.

        - filename: a string filename, such as utils.py

        - returns: a string containing the provided filename's extension
    """

    return os.path.splitext(filename)[1]


def setVersionArchive(versionid: str, archived: bool):
    """ Utility function for flipping boolean value of archived version from true to false

        - versionid: the version ID of the file version to unarchive / restore

        - returns: a dictionary of the versions with the versionids as keys and JSON data as the values
    """

    try:
        version = FileVersionTable.query.filter(FileVersionTable.versionid == versionid).first()
        version.archived = archived
        db.session.commit()

        return True
    except Exception as e:
        return False


def getFileVersions(fileID: str, archived: bool=False):
    """ Utility function used throughout the system which given a fileid, and an option to fetch only archived versions,
        gets all the versions associated with that file

        - fileid: UUID of the file in which to search for versions from
        - archived: a boolean to decide whether the function should fetch archived versions or regular versions

        - returns: a dictionary of the versions with the versionids as keys and JSON data as the values
    """

    try:
        versionQuery = FileVersionTable.query.filter(FileVersionTable.fileid == fileID).filter(
            FileVersionTable.archived == archived)  # Fetches the versions from the fileversiontable

        versions = versionQuery.all()   # Executes the query and retrieves the data
        results = {}                    # The results that the function will return

        for version in versions:        # For each version fetch its metadata and add it as fields to the dictionary
            metadata = getMetadata(str(version.versionid)).all()

            versionData = {
                "versionid": str(version.versionid),
                "versionhash": str(version.versionhash),
            }

            for data in metadata:
                if data.title == "userid":      # If the metadata title is userid, replace it with extensive user data
                    versionData["author"] = getUserData(data.value)
                else:
                    versionData[data.title] = data.value

            results[str(version.versionid)] = versionData   # Add a new key/value to the dictionary for this version

        return results  # Return the calculated version data dictionary
    except Exception as e:
        print(print_exc())

        return {}       # If an error occurs, simply return an empty dictionary


def getFileGroups(fileID):
    """ Fetches all the groups with access to a file.

        - fileid: UUID of the file in which to yield the group data for

        - returns: a list of dictionaries, each containing data on a group with access to the specified file
    """

    return [group.serialise() for group in GroupTable.query.join(FileGroupTable,
                                                                 and_(GroupTable.groupid == FileGroupTable.groupid,
                                                                      FileGroupTable.fileid == fileID)).all()]


def newFileVersion(fileData, uploadData, title, userid):
    """ Reusable utility function for, given the appropriate data, creating a new file version - handling all the B2,
        and database interaction.

        - userid: the UUID of the user who triggered the file version creation, i.e: the version creator
        - fileData: a dictionary of data about the file to the version to
        - uploadData: the data uploaded by the user for the new file (the file and the version's title)
        - title: what the version should be listed as on the file page

        - returns: a boolean to indicate whether the file was uploaded successfully
    """

    b2 = B2Interface(                           # Initialise an instance of the B2 interface in order to upload the file
        os.environ.get("APPLICATION_KEY_ID"),
        os.environ.get("APPLICATION_KEY"),
        os.environ.get("BUCKET_NAME")
    )

    fileversion = FileVersionTable({            # Create a new fileversion instance, linking the version to the
        "fileid": fileData["fileid"],           # corresponding row in the filetable and passing a temporary versionhash
        "versionhash": "temp"                   # field, which is replaced after the file is uploaded to b2
    })

    upload = b2.uploadFile(data=uploadData.read(),
                           versionid=fileversion.versionid,
                           filename=fileData["filename"],
                           fileid=str(fileData["fileid"]),
                           extension=fileData["extension"])     # Passes all the required information to the b2 in order
                                                                # to upload the file

    if not isUniqueVersion(fileData["fileid"], str(upload.get_content_sha1())):
        b2.removeVersion(str(fileversion.versionid))
        return False

    fileversion.versionhash = upload.get_content_sha1()        # Replaces the temporary hash field in the FileVersion record

    db.session.add(fileversion)                                # Adds and commits the row to the db
    db.session.commit()

    authorData = MetadataTable({                # Adds the appropriate title, userid, and uploaded metadata to the version
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

    userData = getUserData(userid)                  # Sends an email to the other group members indicating that a new
                                                    # version has been uploaded
    for group in getFileGroups(fileData["fileid"]):
        sendGroupEmail(group["groupid"], {
            "subject": "New Version of " + fileData["filename"] + " Created",
            "content": "Hi there!\n" + userData["username"] + " (" + userData[
                "email"] + ") has created a new version of " +
                       fileData["filename"] + " with the title \"" + titleData.value + "\". \n\nThanks,\nfile-rep0"
        }, userData)

    return True


def isUniqueVersion(fileid: str, versionhash: str):
    versions = getFileVersions(fileid)

    for version in versions.values():
        if version["versionhash"] == versionhash:
            return False

    return True


def leaderCheck(groupList, userid):
    """ Checks, given a list of groups, if the specified user id is a groupleader, using boolean operations and list
        comprehensions

        - groupList: list of group data dictionaries which contain the "groupleaderid" field to compare the userid to
        - userid: the UUID of the user whom to check for group leadership

        - returns: a boolean indicating whether or not they are a group leader
    """

    return True in [group["groupleaderid"] == userid for group in groupList]
