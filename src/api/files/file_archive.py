from traceback import print_exc
import json

from flask import request, redirect, url_for

from src.api.files.file_query import file_query
from src.api.user.utils import getUserData

from src.api.files import filesBP
from src.api.files.utils import setVersionArchive

@filesBP.route("/restoreFile", methods=["POST"])
def restoreFile():
    """ Endpoint which given a fileid will restore all the archived versions of that specific file, by running the
        restoreVersion util function iteratively, setting the archived field in the respective FileVersionTable records
        to false

        - fileid: UUID of the file in which to unarchive any archived versions from
        - userid: UUID of the user triggering the file restoration, must be an admin

        - returns: a response which may be either successful or with an error message, depending on outcome of operation
    """

    isBrowser = "fileid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this"
            }), 403

    if not getUserData(request.cookies.get("userid"))["admin"]:
        if isBrowser:
            return redirect(url_for("dash", msg="You don't have permission to do this"))
        else:
            return json.dumps({"code": 200, "msg": "You don't have the permissions to do this"})

    try:
        files = file_query({"fileid": data["fileid"], "archived": True})[0]

        for version in files["versionorder"]:
            if not setVersionArchive(version, False):
                raise Exception()

        if isBrowser:
            return redirect(url_for("file", id=data["fileid"], msg="Archived versions successfully restored"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "Archived versions successfully restored"
            })

    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("archive", msg="Something went wrong when restoring your files"))
        else:
            return json.dumps({"code": 500, "msg": "Something went wrong when restoring your files"})


@filesBP.route("/restoreVersion", methods=["POST"])
def restoreFileVersion():
    """ An endpoint which interfaces with the restoreVersion util function in order to restore a specified file version
        from the archive into the main file store

        - versionid: UUID of the version which should be restored from the archive
        - userid: UUID of the user triggering the file restoration, must be an admin

        - returns: a response which may be either successful or with an error message, depending on outcome of operation
    """

    isBrowser = "versionid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this"
            }), 403

    if not getUserData(request.cookies.get("userid"))["admin"]:
        if isBrowser:
            return redirect(url_for("dash", msg="You don't have permission to do this"))
        else:
            return json.dumps({"code": 200, "msg": "You don't have the permissions to do this"})

    try:
        if not setVersionArchive(data["versionid"], False):
            raise Exception()

        if isBrowser:
            return redirect(url_for("version", id=data["versionid"], msg="Archived version successfully restored"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "Archived versions successfully restored"
            })

    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("archivedFile", id=data["fileid"], msg="Something went wrong while restoring this version"))
        else:
            return json.dumps({"code": 500, "msg": "Something went wrong when restoring the version"})


@filesBP.route("/archiveFile", methods=["POST"])
def archiveFile():
    """ Endpoint which given a fileid will archive all the non-archived versions of that specific file, by running the
        archiveVersion util function iteratively, setting the archived field in the respective FileVersionTable records
        to true

        - fileid: UUID of the file in which to archive any unarchived versions from
        - userid: UUID of the user triggering the file archiving, must be an admin

        - returns: a response which may be either successful or with an error message, depending on outcome of operation
    """

    isBrowser = "fileid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this"
            }), 403

    if not getUserData(request.cookies.get("userid"))["admin"]:
        if isBrowser:
            return redirect(url_for("dash", msg="You don't have permission to do this"))
        else:
            return json.dumps({"code": 403, "msg": "You don't have the permissions to do this"}), 403

    try:
        files = file_query({"fileid": data["fileid"]})[0]

        for version in files["versionorder"]:
            if not setVersionArchive(version, True):
                raise Exception()

        if isBrowser:
            return redirect(url_for("archive", msg="All versions successfully archived"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "All versions successfully archived"
            })

    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("archive", msg="Something went wrong when restoring your files"))
        else:
            return json.dumps({"code": 500, "msg": "Something went wrong when restoring your files"})


@filesBP.route("/archiveVersion", methods=["POST"])
def archiveVersion():
    """ Endpoint which will set the archived field in the corresponding db row, given a version id, to true

        - versionid: UUID of the file version in which to archive
        - userid: UUID of the user triggering the file archiving, must be an admin

        - returns: a response which may be either successful or with an error message, depending on outcome of operation
    """

    isBrowser = "versionid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this"
            }), 403

    if not getUserData(request.cookies.get("userid"))["admin"]:
        if isBrowser:
            return redirect(url_for("dash", msg="You don't have permission to do this"))
        else:
            return json.dumps({"code": 403, "msg": "You don't have the permissions to do this"}), 403

    try:
        if not setVersionArchive(data["versionid"], True):
            raise Exception()

        if isBrowser:
            return redirect(url_for("archive", msg="Version successfully archived"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "Version has been successfully archived"
            })

    except Exception as e:
        print(print_exc())

        if isBrowser:
            return redirect(url_for("archive", msg="Something went wrong when restoring your files"))
        else:
            return json.dumps({"code": 500, "msg": "Something went wrong when restoring your files"})
