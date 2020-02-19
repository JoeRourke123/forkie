from flask import Blueprint, request, redirect, url_for, make_response

import json
from traceback import print_exc

from src.db.MetadataTable import MetadataTable

from src.db import db


metadataBP = Blueprint("metadata", __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/metadata')


@metadataBP.route("/add", methods=["POST"])
def addMetadata(browserData=request.form):
    isBrowser = "versionid" in browserData
    data = browserData if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You must be signed in to complete this action"))

    try:
        metadata = MetadataTable(data)

        db.session.add(metadata)
        db.session.commit()

        if isBrowser and browserData is request.form:
            return redirect(url_for("version", id=data["versionid"], msg="Metadata added!"))
        elif not isBrowser:
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