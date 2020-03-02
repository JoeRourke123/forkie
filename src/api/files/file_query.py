from traceback import print_exc

from flask import request, make_response

from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db.FileVersionTable import FileVersionTable

from src.api.files import filesBP
from src.api.user.utils import getFilesUserCanAccess, getUserData
from src.api.files.utils import getFileGroups, getFileVersions
import src.api.groups.utils  # import getGroupDataFromName

import json
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
        "archived": {"type": "boolean"},
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

            # Return bad request if the user id is None
            if userid is None:
                raise Exception

            query = getFilesUserCanAccess(userid)
            get_first = False
            if len(data) > 0:
                if "filename" in data:
                    # Searches by wildcard so any filename containing that string will be included
                    query = query.filter(FileTable.filename.like("%" + str(data["filename"]) + "%"))
                if "fileid" in data:
                    query = query.filter(FileTable.fileid == str(data["fileid"]))
                if "versionid" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionid == data["versionid"])
                if "extension" in data:
                    query = query.filter(FileTable.extension == data["extension"])
                if "versionhash" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.versionhash == data["versionhash"])
                if "groupid" in data:
                    query = query.filter(FileTable.fileid == FileGroupTable.fileid, FileGroupTable.groupid == data["groupid"])
                if "groupname" in data:
                    # Get groupid using getGroupDataFromName
                    groupid = src.api.groups.utils.getGroupDataFromName(data['groupname']).serialise()['groupid']
                    query = query.filter(FileTable.fileid == FileGroupTable.fileid, FileGroupTable.groupid == groupid)
                if "first" in data:
                    get_first = data['first']
                if "archived" in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.archived == data["archived"])
                elif "archived" not in data:
                    query = query.filter(FileTable.fileid == FileVersionTable.fileid, FileVersionTable.archived == False)
            # Queries all even when first flag is true as it needs all columns from query object 
            # and first() method strips other columns for some reason
            query = query.all()
            # Construct return rows to be passed to the returned JSON response
            rs_list = []
            print('\n\nGetting files for user: ' + userid + ' query of', data)
            for x, row in enumerate(query):
                # print('\nFile ' + str(x) + ':')
                if row is not None:
                    # print("FileID:", str(row.fileid))
                    # print("Filename:", row.filename)
                    # print("Groups:", getFileGroups(str(row.fileid)))
                    # print("Versions:", getFileVersions(str(row.fileid)))
                    rs_json = {
                        "fileid": str(row.fileid),
                        "filename": row.filename,
                        "extension": row.extension,
                        "groups": getFileGroups(str(row.fileid)),
                        "versions": getFileVersions(str(row.fileid), archived=("archived" in data and data["archived"])),
                    }

                    rs_json["versionorder"] = sorted(rs_json["versions"].keys(),
                                                     key=lambda vID: rs_json["versions"][vID]["uploaded"], reverse=True)

                    rs_list.append(rs_json)

                rs_list = sorted(rs_list, key=lambda x: x["versions"][x["versionorder"][0]]["uploaded"], reverse=True)

            if browserQuery is not None:
                return rs_list

            # Fixes JSON serialisation issues. Did this this way to not interfere with any other modules
            print("rslist", rs_list)
            for rs in rs_list:
                for versionid in rs['versions'].keys():
                    ver = rs['versions'][versionid]
                    # Userid key is UUID object so convert to string
                    ver['author']['userid'] = str(ver['author']['userid'])
                    # lastlogin key is datetime object so convert to string
                    ver['author']['lastlogin'] = str(ver['author']['lastlogin'])
            resp = make_response(json.dumps({"code": 200, "msg": "Here are the returned rows", "rows": rs_list}))
            resp.set_cookie("userid", userid)

            return resp
        except Exception as e:
            print(print_exc())

            if browserQuery is not None:
                return []
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when querying files"
                }), 500
    except ValidationError:
        if browserQuery is not None:
            []
        else:
            return json.dumps({
                "code": 400,
                "msg": "There was something wrong with the data you sent, please check and try again"
            })
