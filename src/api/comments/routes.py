from flask import Blueprint, request, redirect, url_for, make_response

import json
from traceback import print_exc

from src.api.files.file_query import file_query
from src.api.comments.utils import addComment

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
                "code": 401,
                "msg": "You must be signed in to complete this action"
            }), 401

    userFiles = list(map(lambda x: x["fileid"], file_query({"userid": request.cookies.get("userid")})))

    if data["fileid"] not in userFiles:
        if isBrowser:
            return redirect(url_for("index", msg="You do not have permission to complete this action"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You do not have permission to complete this action"
            }), 403

    try:
        addComment(data, request.cookies.get("userid"))

        if isBrowser:
            return redirect(
                url_for("file", id=data["fileid"], msg="Your comment has been added!")
            )
        else:
            return json.dumps({
                "code": 200,
                "msg": "Your comment has been added!",
            })
    except Exception as e:
        print(print_exc())
        return str(e)

        if isBrowser:
            return redirect(
                url_for("version", id=data["versionid"], msg="Sorry, something went wrong when adding your metadata"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when adding metadata",
                "err": print_exc()
            }), 500