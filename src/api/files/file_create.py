from traceback import print_exc
import json

from flask import request, redirect, url_for

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
