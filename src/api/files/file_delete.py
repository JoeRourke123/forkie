import os
from traceback import print_exc
import json

from flask import request, redirect, url_for
from sqlalchemy import and_

from src.api.files.backblaze import B2Interface
from src.api.files.file_query import file_query
from src.api.user.utils import getUserData

from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db import db

from src.api.files import filesBP
from src.api.files.utils import newFileVersion, getFileVersions, leaderCheck
from src.db.FileVersionTable import FileVersionTable


@filesBP.route("/deleteFile", methods=["POST"])
def deleteFile(fileid=None):
    """ Endpoint for the complete deletion of a file once an admin deletes it from the archive. Accessible three ways,
        it is callable (for when duplicate versions might be found), accessible from the web app, and also from the CLI

        - userid: the UUID of the user who created the file, used to check for admin privileges
        - fileid: the UUID of the file in which to delete

        - returns: an accurate response/redirection depending on the level of success of file removal/db record removal
    """
    if fileid is not None:
        isBrowser = True
        data = {"fileid": fileid}
    else:
        isBrowser = "fileid" in request.form
        data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for('index', msg="You must be signed in to do this!"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to do this",
            }), 401

    fileData = file_query({"fileid": data["fileid"], "archived": True})[0]
    userData = getUserData(request.cookies.get("userid"))

    if not userData["admin"]:
        if isBrowser:
            return redirect(url_for("dash", msg="You don't have permission to do this!"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You don't have permission to delete this file",
            })

    try:
        file = FileTable.query.filter(FileTable.fileid == fileData["fileid"]).first()
        db.session.delete(file)
        db.session.commit()     # Remove the FileTable record from the database, and due to the cascading deletion
                                # rules, any associated metadata, versions, comments, group linkings should be removed also
        b2 = B2Interface(
            os.environ.get("APPLICATION_KEY_ID"),       # Create an instance of the B2Interface in order to communicate
            os.environ.get("APPLICATION_KEY"),          # with the Backblaze bucket
            os.environ.get("BUCKET_NAME")
        )

        for version in fileData["versions"].values():            # Run the B2Interface remove method in order to delete each
            b2.removeVersion(version["versionid"])      # file versions' actual file from the B2 bucket

        if isBrowser:                                   # If all goes successfully, the user should be redirected or...
            return redirect(url_for("archive", msg=fileData["filename"] + " successfully deleted!"))
        else:
            return json.dumps({                         # receive a JSON response indicating success
                "code": 200,
                "msg": fileData["filename"] + " has been successfully deleted"
            })
    except Exception as e:
        print(print_exc())      # Print the stack trace if an error occurs and redirect the user to the dashboard

        if isBrowser:
            return redirect(url_for("dash", msg="Something went wrong when deleting the file"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when deleting the file"
            }), 500


@filesBP.route("/deleteVersion", methods=["POST"])
def deleteVersion():
    """ Endpoint which can delete a file version by an admin, once moved to the archive

        - versionid: the UUID of the version in which to delete
        - userid: the UUID of the admin user who triggered the version delete

        - returns: an accurate response/redirection depending on the level of success in deleting the version
    """

    isBrowser = "versionid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for('index', msg="You must be signed in to do this!"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to do this",
            }), 401

    fileData = file_query({"versionid": data["versionid"], "archived": True})[0]
    versionCount = len(fileData["versionorder"])            # Version order is a list of versionids therefore can be
                                                            # used as an accurate count for the number of versions
    if versionCount <= 1:
        return deleteFile(fileData["fileid"])               # Deletes the entire file in the case of there only being
                                                            # one version left
    try:
        userData = getUserData(request.cookies.get("userid"))

        if not userData["admin"]:                           # User has to be an admin to access this endpoint
            if isBrowser:
                return redirect(url_for("dash", msg="You don't have permission to do this!"))
            else:
                return json.dumps({
                    "code": 403,
                    "msg": "You don't have permission to delete this file version",
                })

        fileVersion = FileVersionTable.query.get(data["versionid"])     # Gets file version row from the table
        db.session.delete(fileVersion)                                  # Deletes it and commits changes
        db.session.commit()

        b2 = B2Interface(
            os.environ.get("APPLICATION_KEY_ID"),
            os.environ.get("APPLICATION_KEY"),
            os.environ.get("BUCKET_NAME")
        )

        b2.removeVersion(data["versionid"])                            # Removes the version's B2 file

        if isBrowser:                   # Returns with a response upon successful deletion
            return redirect(url_for("archivedFile", id=fileData["fileid"], msg="File version successfully deleted!"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "The file version has been successfully deleted"
            })
    except Exception as e:              # Provides error response for failed deletion
        print(print_exc())

        if isBrowser:
            return redirect(url_for("file", id=fileData["fileid"], msg="Something went wrong when deleting the file version"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when deleting the file version"
            }), 500


@filesBP.route("/removeGroup", methods=["POST"])
def removeGroup():
    """ Endpoint for removing access from a file for a group

        - groupid: the UUID of the group in which the file will no longer be able to access
        - userid: the UUID of the user who triggered the group permissions change
        - fileid: UUID of the file in which to revoke the group's access to

        - returns: an accurate response/redirection depending on the level of success in changing the file permissions
    """

    isBrowser = "fileid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for('index', msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to do this",
            }), 401

    file = file_query({"fileid": data["fileid"]})[0]
    userData = getUserData(request.cookies.get("userid"))

    if not file or not (userData["admin"] or leaderCheck(file["groups"], str(userData["userid"]))):
        if isBrowser:
            return redirect(url_for("dash", msg="You don't have permission to do this!"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You don't have permission to add groups",
            })

    try:
        groupExists = True in [str(group["groupid"]) == data["groupid"] for group in file["groups"]]
        # Runs checks to see if this group is in the file's groups, and raises an exception if not
        if not groupExists:
            raise Exception()

        filegroup = FileGroupTable.query.filter(and_(FileGroupTable.groupid == data["groupid"],
                                                     FileGroupTable.fileid == data["fileid"])).first()
        # Retrieves the corresponding record from the group-file linking table so it can be deleted
        db.session.delete(filegroup)
        db.session.commit()

        if isBrowser:
            return redirect(url_for('file', id=data["fileid"], msg="Group removed successfully!"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "Group was removed successfully!",
            })
    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("file", id=data["fileid"], msg="Sorry, something went wrong when removing this group"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Sorry, something went wrong when removing this group"
            }), 500

