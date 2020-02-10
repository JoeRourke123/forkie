from flask import current_app as app
from flask import render_template, Blueprint, request, make_response, redirect, url_for

from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db.FileVersionTable import FileVersionTable
from src.utils import hashPassword
from src.db import db
from src.api.user.utils import getFilesUserCanAccess

from datetime import datetime
import json
from jsonschema import validate, ValidationError
# from sqlalchemy.orm import sessionmaker
# Session = sessionmaker(bind=engine)
# session = Session()

fQueryBP = Blueprint('file_query', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api')
query_schema = {
    "type": "object",
    "properties": {
        "filename": {"type": "string"},
        "versionid": {"type": "string"},
        "fileid": {"type": "number"},
        "extension": {"type": "string"},
        "groupid": {"type": "number"},
        "versionhash": {"type": "number"},
        "first": {"type": "boolean"}
    }
}

""" Types of ways to query files
    - by all (when nothing is inside JSON query)
    - by filename (file table)
    - by version ID (file version table)
    - by extension (file version table)
    - by versionhash (file version table)
    - by groupid (file group table)
    - by file ID (all file tables)
    - by first query result (boolean)
"""

@fQueryBP.route("/file_query", methods=["POST"])
def file_query():
    isBrowser = bool(request.form is not None)
    data = request.form if isBrowser else request.json
    
    # Validate data
    try:
        validate(instance=data, schema=query_schema)
        try:
            # Return unauthorized access code if the userid is not found in the cookies
            if "userid" not in request.cookies and not isBrowser:
                return json.dumps({
                    "code": 401,
                    "msg": "Unauthorized. Make sure you sure you have logged in."
                })
            userid = request.cookies.get("userid")
            # query = session.query(FileTable)
            # all_rows = query.all()
            query = getFilesUserCanAccess(userid)
            if len(data) > 0:
                if "filename" in data:
                    query = query.filter(FileTable.filename == data["filename"])
                if "fileid" in data:
                    query = query.filter(FileTable.fileid == data["fileid"])
                if "versionid" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionid == data["versionid"])
                if "extension" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionid == data["extension"])
                if "versionhash" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionid == data["versionhash"])
                if "groupid" in data:
                    query = query.filter(FileTable.fileid == FileGroupTable.fileid, FileGroupTable.groupid == data["groupid"])
                if "first" in data:
                    if data["first"]:
                        query = query.first()

            rs = query.all()
            print(rs)
            print([(dict(row.items())) for row in rs])
            resp = make_response(json.dumps({"code": 200, "msg": "Here are the returned rows", "rows": [(dict(row.items())) for row in rs]}))
            resp.set_cookie("userid", userid)
            resp.set_cookie("client", "browser" if isBrowser else "cli")
            
            return resp
        except Exception as e:
            # print(e.with_traceback())
            print(e)

            if isBrowser:
                return redirect(url_for("errors.error", code=500, url="file_query.file_query"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when querying files"
                }), 500
    except ValidationError:
        if isBrowser:
            return redirect(url_for("errors.error", code=400, url="file_query.file_query"))
        else:
            return json.dumps({
                "code": 400,
                "msg": "There was something wrong with the data you sent, please check and try again"
            })
