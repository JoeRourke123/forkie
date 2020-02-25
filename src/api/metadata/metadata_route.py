from flask import Blueprint, request

import json

from src.db.MetadataTable import MetadataTable

from get_metadata import getMetadata

filesBP = Blueprint("files", __name__,
                    template_folder = "../../templates",
                    static_folder = "../../static",
                    url_prefix = "/api/groups")


@filesBP.route("/metadata", methods = ["POST"])
def getMetadata():
    isBrowser = "versionID" in request.form

    if isBrowser:
        data = request.form
    else:
        data = request.data

    result = getMetadata

    result_json = {"title": result[0][2],
                   "value": result[0][3]}

    return result_json

