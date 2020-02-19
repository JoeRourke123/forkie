from traceback import print_exc

from flask import render_template, Blueprint, request, make_response, redirect, url_for

from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db.FileVersionTable import FileVersionTable

from src.api.files import filesBP
from src.api.user.utils import getFilesUserCanAccess
from src.api.files.utils import getFileGroups, getFileVersions

import json
from uuid import UUID
from jsonschema import validate, ValidationError

query_schema = {
    "type": "object",
    "properties": {
        "filename": {"type": "string"},
        "versionid": {"type": "string"},
        "fileid": {"type": "string"},
        "extension": {"type": "string"},
        "groupid": {"type": "string"},
        "groupname": {"type": "string"},
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
    - by groupname (file group table)
    - by file ID (all file tables)
    - by first query result (boolean)
    The query JSON data will first be validated against the query_schema. If the JSON is invalid an error 500
    is returned. Then will check for userid inside cookie. If userid is not found or userid is None then error 401 or error 400
    is returned. All the files the user can access are then queried using getFilesUserCanAccess. If the JSON query data is empty
    then all the files the user can access are returned (cols: fileid, filename, groupname, groupid). Otherwise the query is
    shortlisted by the criteria inside the JSON query. Rows from query obj are then converted to a JSON to be returned
"""


@filesBP.route("/query", methods=["POST"])
def file_query(browserQuery=None):
    data = browserQuery if browserQuery is not None else json.loads(request.data)

    # Validate data
    try:
        validate(instance=data, schema=query_schema)
        try:
            # Return unauthorized access code if the userid is not found in the cookies
            if "userid" not in request.cookies and browserQuery is not None:
                return json.dumps({
                    "code": 401,
                    "msg": "Unauthorized. Make sure you sure you have logged in."
                })

            userid = request.cookies.get("userid")
            print(userid)

            # Return bad request if the user id is None
            if userid is None:
                raise Exception

            query = getFilesUserCanAccess(userid)
            get_first = False
            print(data)
            if len(data) > 0:
                # Works (tested)
                if "filename" in data:
                    # Searches by wildcard so any filename containing that string will be included
                    query = query.filter(FileTable.filename.like("%" + str(data["filename"]) + "%"))
                # Works (tested)
                if "fileid" in data:
                    query = query.filter(FileTable.fileid == str(data["fileid"]))
                # No worky (not tested)
                if "versionid" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionid == data["versionid"])
                # No worky (not tested)
                if "extension" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionid == data["extension"])
                # No worky (not tested)
                if "versionhash" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionid == data["versionhash"])
                # Works (not tested)
                if "groupid" in data:
                    query = query.filter(FileTable.fileid == FileGroupTable.fileid, FileGroupTable.groupid == data["groupid"])
                # Works (not tested)
                if "groupname" in data:
                    query = query.filter(FileTable.fileid == FileGroupTable.fileid, FileGroupTable.groupname == data["groupname"])
                # Works (tested)
                if "first" in data:
                    get_first = data['first']
                    
            # Queries all even when first flag is true as it needs all columns from query object 
            # and first() method strips other columns for some reason
            query = query.all()
            # Construct return rows to be passed to the returned JSON response
            rs_list = []
            for r in range(0, len(query) if not get_first else 1):
                row = query[r]
                if row is not None:
                    print(row)
                    rs_json = {
                        "fileid": str(row[1]),
                        "filename": row[2],
                        "groups": getFileGroups(str(row[1])),
                        "versions": getFileVersions(str(row[1]))
                    }
                    rs_list.append(rs_json)

            rs_list = sorted(rs_list, key=lambda x: x["versions"][0]["uploaded"], reverse=True)

            if browserQuery is not None:
                return rs_list

            resp = make_response(json.dumps({"code": 200, "msg": "Here are the returned rows", "rows": rs_list}))
            resp.set_cookie("userid", userid)

            return resp
        except Exception as e:
            print(print_exc())

            if browserQuery:
                return redirect(url_for("errors.error", code=500, url="file_query.file_query"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when querying files"
                }), 500
    except ValidationError:
        if browserQuery is not None:
            return redirect(url_for("errors.error", code=400, url="file_query.file_query"))
        else:
            return json.dumps({
                "code": 400,
                "msg": "There was something wrong with the data you sent, please check and try again"
            })
