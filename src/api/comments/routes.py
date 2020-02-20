from flask import Blueprint, request, redirect, url_for, make_response

import json
from traceback import print_exc

from src.db.MetadataTable import MetadataTable

from src.db import db

commentsBP = Blueprint("comments", __name__,
                       template_folder='../../templates',
                       static_folder='../../static',
                       url_prefix='/api/comment')

@commentsBP.route("/new", methods=["POST"])
def newComment():
    isBrowser = "comment" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to complete this action"
            }), 403