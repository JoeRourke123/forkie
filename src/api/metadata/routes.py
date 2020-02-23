from flask import Blueprint, request, redirect, url_for, make_response

import json
from traceback import print_exc

from src.api.files.file_query import file_query
from src.db.MetadataTable import MetadataTable

from src.db import db


metadataBP = Blueprint("metadata", __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/metadata')


@metadataBP.route("/add", methods=["POST"])
def addMetadata():
    isBrowser = "versionid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to complete this action"
            }), 403
    try:
        metadata = MetadataTable(data)

        db.session.add(metadata)
        db.session.commit()

        if isBrowser:
            return redirect(url_for("version", id=data["versionid"], msg="Metadata added!"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "Metadata created!"
            })
    except Exception as e:
        print(print_exc())
        return str(e)

        if isBrowser:
            return redirect(url_for("version", id=data["versionid"], msg="Sorry, something went wrong when adding your metadata"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when adding metadata",
                "err": print_exc()
            }), 500


@metadataBP.route("/edit", methods=["POST"])
def editMetadata():
    isBrowser = "versionid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to complete this action"
            }), 403

    file = file_query({"versionid": data["versionid"]})

    if not file:
        if isBrowser:
            return redirect(url_for("index", msg="You either do not have access to this file, or it does not exist"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You either do not have access to this file or it does not exist"
            }), 401

    try:
        metadata = MetadataTable.query.filter(MetadataTable.versionid == data["versionid"],
                                              MetadataTable.title == data["title"]).first()

        metadata.value = data["value"]
        db.session.commit()

        if isBrowser:
            return redirect(url_for("version", id=data["versionid"], msg="Metadata '" + data["title"] + "' changed!"))
        else:
            return json.dumps({
                "code": 200,
                "msg": "The metadata for this file has been successfully altered"
            })
    except Exception as e:
        print(print_exc())
        return str(e)

        if isBrowser:
            return redirect(url_for("version", id=data["versionid"],
                                    msg="Sorry, something went wrong when adding your metadata"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when adding metadata",
                "err": print_exc()
            }), 500