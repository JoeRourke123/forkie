from flask import Blueprint, request, redirect, url_for, make_response

import json
from traceback import print_exc

from sqlalchemy import and_

from src.api.files.file_query import file_query
from src.api.comments.utils import addComment
from src.db.CommentTable import CommentTable

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
                url_for("dash", msg="Sorry, something went wrong when adding your comment"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when adding comment",
                "err": print_exc()
            }), 500


@commentsBP.route("/bulkComment", methods=["POST"])
def bulkComment():
    isBrowser = "comment" in request.form
    data = request.form if isBrowser else dict(json.loads(request.data))

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to complete this action"
            }), 401

    fileids = data.getlist("fileids") if isBrowser else data["fileids"]
    data = dict(data)

    try:
        for fileid in fileids:
            data["fileid"] = fileid
            addComment(data, request.cookies.get("userid"))

        if isBrowser:
            return redirect(
                url_for("dash", msg="Your comments have been added")
            )
        else:
            return json.dumps({
                "code": 200,
                "msg": "Your comments has been added!",
            })
    except Exception as e:
        if isBrowser:
            return redirect(
                url_for("dash", msg="Sorry, something went wrong when adding your comments"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when adding comments",
                "err": print_exc()
            }), 500


@commentsBP.route("/delete", methods=["POST"])
def deleteComment():
    isBrowser = "commentid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to complete this action"
            }), 401

    comment = CommentTable.query.filter(and_(
        CommentTable.commentid == data["commentid"], CommentTable.userid == request.cookies.get("userid")
    )).first()


    if not comment:
        if isBrowser:
            return redirect(url_for("dash", msg="You do not have permission to complete this action"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You do not have permission to complete this action"
            }), 403

    try:
        db.session.delete(comment)
        db.session.commit()

        if isBrowser:
            return redirect(
                url_for("file", id=data["fileid"], msg="Your comment has been deleted!")
            )
        else:
            return json.dumps({
                "code": 200,
                "msg": "Your comment has been deleted!",
            })
    except Exception as e:
        if isBrowser:
            return redirect(
                url_for("dash", msg="Sorry, something went wrong when removing your comment"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when removing your comment",
                "err": print_exc()
            }), 500