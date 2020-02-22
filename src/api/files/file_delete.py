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
from src.api.files.utils import newFileVersion
from src.db.FileVersionTable import FileVersionTable


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

    try:
        userData = getUserData(request.cookies.get("userid"))

        hasPermissions = False

        for version in fileData["versions"]:
            if version["versionid"] == data["versionid"] and version["author"] == userData:
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

        db.session.delete(FileVersionTable.query.filter(FileVersionTable.versionid == data["versionid"]).first())
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

