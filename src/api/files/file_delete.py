import os
from traceback import print_exc
import json

from flask import request, redirect, url_for

from src.api.files.backblaze import B2Interface
from src.api.files.file_query import file_query
from src.api.user.utils import getUserData

from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db import db

from src.api.files import filesBP
from src.api.files.utils import newFileVersion, getFileVersions
from src.db.FileVersionTable import FileVersionTable

@filesBP.route("/deleteFile", methods=["POST"])
def deleteFile(fileid=None):
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

    fileData = file_query({"fileid": data["fileid"]})[0]
    userData = getUserData(request.cookies.get("userid"))

    if not fileData or not (userData["admin"] or True in [str(group["groupleaderid"]) == str(userData["userid"]) for group in fileData["groups"]]):
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
        db.session.commit()

        b2 = B2Interface(
            os.environ.get("APPLICATION_KEY_ID"),
            os.environ.get("APPLICATION_KEY"),
            os.environ.get("BUCKET_NAME")
        )

        for version in fileData["versions"]:
            b2.removeVersion(version["versionid"])

        if isBrowser:
            return redirect(url_for("dash", msg=fileData["filename"] + " successfully deleted!"))
        else:
            return json.dumps({
                "code": 200,
                "msg": fileData["filename"] + " has been successfully deleted"
            })
    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("dash", msg="Something went wrong when deleting the file"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when deleting the file"
            }), 500


@filesBP.route("/deleteVersion", methods=["POST"])
def deleteVersion():
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

    fileData = file_query({"versionid": data["versionid"]})[0]

    versionCount = len(getFileVersions(fileData["fileid"]))

    if versionCount <= 1:
        return deleteFile(fileData["fileid"])

    try:
        userData = getUserData(request.cookies.get("userid"))

        hasPermissions = False

        for version in fileData["versions"]:
            if version["versionid"] == data["versionid"] and version["author"]["userid"] == userData["userid"]:
                hasPermissions = True
                break

        hasPermissions = hasPermissions or userData["admin"] or True in [group["groupleaderid"] == userData["userid"] for group in fileData["groups"]]

        if fileData not in file_query({}) or not hasPermissions:
            if isBrowser:
                return redirect(url_for("dash", msg="You don't have permission to do this!"))
            else:
                return json.dumps({
                    "code": 403,
                    "msg": "You don't have permission to delete this file version",
                })

        fileVersion = FileVersionTable.query.get(data["versionid"])
        db.session.delete(fileVersion)
        db.session.commit()

        b2 = B2Interface(
            os.environ.get("APPLICATION_KEY_ID"),
            os.environ.get("APPLICATION_KEY"),
            os.environ.get("BUCKET_NAME")
        )

        b2.removeVersion(data["versionid"])

        if isBrowser:
            return redirect(url_for("file", id=fileData["fileid"], msg="File version successfully deleted!"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "The file version has been successfully deleted"
            })
    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("file", id=fileData["fileid"], msg="Something went wrong when deleting the file version"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when deleting the file version"
            }), 500

