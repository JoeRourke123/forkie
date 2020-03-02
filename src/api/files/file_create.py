from traceback import print_exc
import json

from flask import request, redirect, url_for

from src.api.comments.utils import addComment
from src.api.files.file_query import file_query
from src.api.files.file_delete import deleteVersion, deleteFile
from src.api.files.archiveCron import checkFiles
from src.api.files.file_archive import restoreFile, restoreFileVersion, archiveFile, archiveVersion
from src.api.user.utils import getUserData

from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db import db

from src.api.files import filesBP
from src.api.files.utils import newFileVersion, leaderCheck



@filesBP.route("/new", methods=["POST"])
def newFile():
    """ Endpoint for the creation of a new FILE folder. An initial version is uploaded alongside an initial comment.
        The user may select a group to share the file with, and add more later.

        - groupid: the UUID of the group in which the file will be initially associated with
        - userid: the UUID of the user who created the file, and will be associated with the initial version
        - comment: an optional comment allowing the user to explain the initial upload.
        - file: the file to upload for the initial version, which will be passed into the Backblaze interface

        - returns: an accurate response/redirection depending on the level of success
    """

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

    # If the file is not in the file upload data from the browser or the CLI
    if "file" not in request.files:
        if isBrowser:
            return redirect(url_for('dash', msg="No files were included in the request"))
        else:
            return json.dumps({
                "code": 406,
                "msg": "No files were included in the request",
            }), 406

    upload = request.files["file"]  # Retrieve the file from the request

    try:
        file = FileTable({
            "filename": upload.filename,
            "extension": upload.filename.split(".")[-1],
        })  # Add the initial file to the FileTable

        db.session.add(file)
        db.session.commit()     # Must be committed before any other additions may be made due to foreign keys

        filegroup = FileGroupTable({
            "fileid": str(file.fileid),
            "groupid": data["groupid"]
        })                      # Adds a FileGroup record to link the group and the file

        db.session.add(filegroup)
        db.session.commit()

        file = {
            "fileid": str(file.fileid),
            "filename": file.filename,
            "extension": file.extension,
        }

        # If the initial file version uploads successfully, titled "Initial Upload", then continue...
        if newFileVersion(file, upload, "Initial Upload", request.cookies.get("userid")):
            if data["comment"]:
                commentData = {
                    "fileid": file["fileid"],
                    "comment": data["comment"]
                }
                addComment(commentData, request.cookies.get("userid"))      # Add the comment if the user included it

            if isBrowser:                                                  # Formulate the appropriate success response
                return redirect(url_for('file', id=file["fileid"]))   # depending on whether the platform is CLI or
            else:                                                          # browser.
                return json.dumps({
                    "code": 200,
                    "msg": file["filename"] + " uploaded successfully",
                }), 200
        else:
            raise Exception()

    except Exception as e:      # Catches exception to allow the UI to continue smoothly even in the case of an error
        print(print_exc())      # Prints the exception to the heroku log

        if isBrowser:
            return redirect(url_for("dash", msg="Something went wrong uploading your file"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when uploading your file"
            }), 500


@filesBP.route("/newVersion", methods=["POST"])
def newVersion():
    """ Endpoint for the creation of a new VERSION within a FILE.

        - userid: the UUID of the user who created the file, and will be associated with the initial version
        - title: what the uploaded version should show as in the file page's list of versions.
        - fileid: the UUID of the file record to associate the version with.
        - file: the file to upload for the new version, which will be passed into the Backblaze interface

        - returns: an accurate response/redirection depending on the level of success of file upload/database alteration
    """

    isBrowser = "fileid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):       # If the user isn't authenticated, redirect them to sign in or produce
        if isBrowser:                           # appropriate JSON response
            return redirect(url_for("index", code=401, msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to do this",
            }), 401

    upload = request.files["file"]              # Retrieve the uploaded file from the request object

    try:
        fileData = file_query({"fileid": data["fileid"]})[0]    # Fetch the data associated with the specified fileid

        if newFileVersion(fileData, upload, data["title"], request.cookies.get("userid")):
            fileData = file_query({"fileid": data["fileid"]})[0]    # If the new version was successfully created,
                                                                    # refetch the file data with the new version in
            if isBrowser:
                return redirect(url_for("version", id=fileData["versions"][fileData["versionorder"][0]]["versionid"],
                                        msg="New version created successfully!"))
            else:
                return json.dumps({
                    "code": 200,
                    "msg": "New version, " + fileData["versions"][fileData["versionorder"][0]]["title"] +
                           ", created successfully!"
                })
        else:      # Won't upload successfully if there already exists a version with an identical hash, user informed of this
            if isBrowser:
                return redirect(url_for("file", id=fileData["fileid"], msg="Sorry, your new version already matches one in this file"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Sorry, your new version matches one already in the file"
                }), 500
    except Exception as e:
        print(print_exc())  # If an exception occurs, then print it to the log and inform the user of an issue

        if isBrowser:
            return redirect(url_for("file", id=fileData["fileid"], msg="Sorry, something went wrong creating your new version"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Sorry, something went wrong when creating your new version"
            }), 500


@filesBP.route("/addGroup", methods=["POST"])
def addGroup():
    """ Endpoint for provided file access to a specified group.

        - groupid: the UUID of the group in which the file will become associated with
        - userid: the UUID of the user who triggered the group permissions change
        - fileid: UUID of the file in which to provide group access to

        - returns: an accurate response/redirection depending on the level of success in changing the file permissions
    """

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

    file = file_query({"fileid": data["fileid"]})[0]
    userData = getUserData(request.cookies.get("userid"))

    # Checks the user has the permission to add groups to a file (must be admin/group leader)
    if not file or not (userData["admin"] or leaderCheck(file["groups"], str(userData["userid"]))):
        if isBrowser:
            return redirect(url_for("file", id=file["fileid"], msg="You don't have permission to do this!"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You don't have permission to add groups",
            })

    try:
        filegroup = FileGroupTable({
            "fileid": data["fileid"],
            "groupid": data["groupid"]
        })

        db.session.add(filegroup)       # Adds a record to the filegrouptable to link the group and the file
        db.session.commit()

        if isBrowser:                   # Redirects the user back to the file page, or sends a JSON success response
            return redirect(url_for('file', id=data["fileid"], msg="Group added successfully!"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "Group was added successfully!",
            })
    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("file", id=data["fileid"], msg="Sorry, something went wrong when adding this group"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Sorry, something went wrong when adding this group"
            }), 500