from flask import Blueprint, request

import json

from src.db.CommentReadTable import CommentReadTable

from comment_read import commentRead

commentsBP = Blueprint("comments", __name__,
                       template_folder = "../../templates",
                       static_folder = "../../static",
                       url_prefix = "/api/comments")

@commentsBP.route("/checkRead")
def commentReadRoute():
    isBrowser = "groupID" in request.form and "versionID" in request.form

    if isBrowser:
        data = request.form
    else:
        data = request.data

    return commentRead(data["versionid"], data["groupid"])
