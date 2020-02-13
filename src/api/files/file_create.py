from flask import Blueprint, request, redirect, url_for

from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db import db

from datetime import datetime
import json

filesBP = Blueprint('files', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api/files')


@filesBP.route("/new", methods=["POST"])
def newFile():
    isBrowser = "filename" in request.form
    data = request.form if isBrowser else request.data
    
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

        # newVersion(file, upload) - function when called will create a new file version for the initial upload

    except Exception as e:
        print(e)
