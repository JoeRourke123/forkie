from flask import Blueprint, request, redirect, url_for, make_response

import json
from traceback import print_exc

from sqlalchemy import and_

from src.api.files.file_query import file_query
from src.api.comments.utils import addComment
from src.db.CommentTable import CommentTable

from src.db import db

# Defines the comments blueprint, encapsulating all the API endpoints related to comments
commentsBP = Blueprint("comments", __name__,
                       template_folder='../../templates',
                       static_folder='../../static',
                       url_prefix='/api/comment')


# POST Endpoint for creating a new comment
@commentsBP.route("/new", methods=["POST"])
def newComment():
    isBrowser = "comment" in request.form   # Endpoint can be reached from a form on web app and the CLI so check must be done to alter response
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):   # Checks if the user is signed in, or at least has the cookie
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:                               # Redirects if on the web app and sends an error msg for the CLI, with a 401 response
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to complete this action"
            }), 401


    commentFile = file_query({"fileid": data["fileid"]})        # Attempts to find a file the user has access to with the provided file id

    if not commentFile:                                         # If it cannot be found, they are informed they do not have correct permissions
        if isBrowser:
            return redirect(url_for("index", msg="You do not have permission to complete this action"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You do not have permission to complete this action"
            }), 403

    try:
        addComment(data, request.cookies.get("userid"))         # Runs the abstracted addComment util function, included for code reusability

        if isBrowser:
            return redirect(                                    # If successful, the user is redirected back to the file page where the comment
                url_for("file", id=data["fileid"], msg="Your comment has been added!")  # can be seen
            )
        else:                                                   # Or a JSON response is sent back to the CLI
            return json.dumps({
                "code": 200,
                "msg": "Your comment has been added!",
            })
    except Exception as e:      # If an error occurs in this function, ideally we'd have more specialised exception handlers
        print(print_exc())      # Prints the error stack trace to the Heroku log

        if isBrowser:           # Redirects the user to the dashboard with a user-friendly error message
            return redirect(
                url_for("dash", msg="Sorry, something went wrong when adding your comment"))
        else:                   # Or sends a JSON response with this message
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when adding comment",
                "err": print_exc()
            }), 500


# Endpoint for the bulk commenting feature, a list of fileIDs and a comment is sent to the route
@commentsBP.route("/bulkComment", methods=["POST"])
def bulkComment():
    isBrowser = "comment" in request.form       # Checks if the comment data is in the form data to check origin platform
    data = request.form if isBrowser else dict(json.loads(request.data))

    if not request.cookies.get("userid"):
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to complete this action"
            }), 401

    # data.getlist is used for multiselect form controls, whereas the CLI just sends the ids as a list
    fileids = data.getlist("fileids") if isBrowser else data["fileids"]
    data = dict(data)       # Data is casted to a dictionary in order for easy indexing later on in the route

    try:
        for fileid in fileids:
            data["fileid"] = fileid                             # Dict casted so the form data can be amended like this
            addComment(data, request.cookies.get("userid"))     # Runs the util addComment function for each fileID

        if isBrowser:
            return redirect(
                url_for("dash", msg="Your comments have been added")
            )
        else:                                                           # Redirect/response upon successful completion
            return json.dumps({
                "code": 200,
                "msg": "Your comments has been added!",
            })
    except Exception as e:                                              # Send an error message if an error occurs
        if isBrowser:
            return redirect(
                url_for("dash", msg="Sorry, something went wrong when adding your comments"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when adding comments",
                "err": print_exc()
            }), 500


# API endpoint for deleting comments from the file page, only accessible to those who have posted the comment
@commentsBP.route("/delete", methods=["POST"])
def deleteComment():
    isBrowser = "commentid" in request.form     # CLI/Browser check
    data = request.form if isBrowser else json.loads(request.data)

    if not request.cookies.get("userid"):       # Checks for presence of the userid cookie
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to complete this action"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "You must be signed in to complete this action"
            }), 401

    comment = CommentTable.query.filter(and_(
        CommentTable.commentid == data["commentid"], CommentTable.userid == request.cookies.get("userid")
    )).first()      # Attempts to fetch the desired comment from the database

    if not comment:     # If it can't be found then the user is informed they don't have permission to delete it
        if isBrowser:
            return redirect(url_for("file", id=data["fileid"], msg="You do not have permission to complete this action"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You do not have permission to complete this action"
            }), 403

    try:
        db.session.delete(comment)      # Comment is deleted from the CommentTable
        db.session.commit()             # Transactions are committed to the database

        if isBrowser:                   # Returns a success response upon completion
            return redirect(
                url_for("file", id=data["fileid"], msg="Your comment has been deleted!")
            )
        else:
            return json.dumps({
                "code": 200,
                "msg": "Your comment has been deleted!",
            })
    except Exception as e:      # If something goes wrong then the user is informed of this
        print(print_exc())

        if isBrowser:
            return redirect(
                url_for("file", id=data["fileid"], msg="Sorry, something went wrong when removing your comment"))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something went wrong when removing your comment",
                "err": print_exc()
            }), 500