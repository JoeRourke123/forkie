from traceback import print_exc
import json

from flask import request, redirect, url_for

from src.api.files.file_query import file_query
from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db import db

from src.api.files import filesBP
from src.api.files.utils import newFileVersion


@filesBP.route("/new", methods=["POST"])
def newFile():
    # isBrowser = 'python-requests' not in request.headers.get('User-Agent')
    isBrowser = "groupid" in request.form
    data = request.form if isBrowser else json.loads(request.data)
    
    # If there is no userid inside the cookie from a cli user then return 401 (unauthorized error)
    if "userid" not in request.cookies:
        if isBrowser:
            return redirect(url_for('errors.error', code=401))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to do this",
            }), 401

    if "file" not in request.files:
        if isBrowser:
            return redirect(url_for('errors.error', code=406, msg="No files were included in the request"))
        else:
            return json.dumps({
                "code": 406,
                "msg": "No files were included in the request",
            }), 406

    upload = request.files["file"]

    try:
        file = FileTable({
            "filename": upload.filename,
            "extension": upload.filename.split(".")[-1],
        })

        db.session.add(file)
        db.session.commit()

        filegroup = FileGroupTable({
            "fileid": str(file.fileid),
            "groupid": data["groupid"]
        })

        db.session.add(filegroup)
        db.session.commit()

        file = {
            "fileid": file.fileid,
            "filename": file.filename,
            "extension": file.extension
        }

        if newFileVersion(file, upload, request.cookies.get("userid")):
            if isBrowser:
                return redirect(url_for('file', id=str(file.fileid)))
            else:
                return json.dumps({
                    "code": 200,
                    "msg": "File uploaded successfully",
                }), 200
        else:
            if isBrowser:
                return redirect(url_for("dash", msg="Something went wrong uploading your file"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when uploading your file"
                }), 500

    except Exception as e:
        print(print_exc())
        return str(e)


@filesBP.route("/newVersion", methods=["POST"])
def newVersion():
    isBrowser = "fileid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for('errors.error', code=401))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to do this",
            }), 401

    upload = request.files["file"]

    try:
        fileData = file_query({"fileid": data["fileid"]})[0]

        if newFileVersion(fileData, upload, request.cookies.get("userid")):
            fileData = file_query({"fileid": data["fileid"]})[0]

            if isBrowser:
                return redirect(url_for("version", id=fileData["versions"][0]["versionid"], msg="New version created successfully!"))
            else:
                return json.dumps({
                    "code": 200,
                    "msg": "New version, " + fileData["versions"][0]["versionid"] + " created successfully!"
                })
        else:
            if isBrowser:
                return redirect(url_for("file", id=fileData["fileid"], msg="Sorry, your new version already matches one in this file"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Sorry, your new version matches one already in the file"
                }), 500
    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("file", id=fileData["fileid"], msg="Sorry, something went wrong creating your new version"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Sorry, something went wrong when creating your new version"
            }), 500