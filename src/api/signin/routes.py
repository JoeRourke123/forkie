import os

from flask import Blueprint, request, make_response, redirect, url_for

from src.db.UserTable import UserTable
from src.api.signup.routes import hashPassword
from src.db import db

from datetime import datetime
import json

signinBP = Blueprint('signin', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api')


@signinBP.route("/signout", methods=["GET"])
def signout():
    """ Endpoint to sign out a user
        - returns: removes the cookie from the response and redirects the user to the signout page
    """

    resp = make_response(redirect(url_for('index', code=200, msg="You have been signed out!")))
    resp.set_cookie("userid", "")

    return resp


@signinBP.route("/signin", methods=["POST"])
def signin():
    """ Endpoint to authenticate and sign in a user

        - email: the user inputted email address
        - password: the user inputted plaintext password

        - returns: a response with a cookie if the user is successfully authenticated, otherwise send back to signin page
    """

    isBrowser = bool("email" in request.form)
    data = request.form if isBrowser else json.loads(request.data)

    if data.get("email") and data.get("password"):       # Server side check for user email and password entry
        try:
            query = UserTable.query.filter_by(email=data['email'])\
                .filter_by(password=hashPassword(data['password'])).first()
            # Query the database with the entered email and password combination

            if not query:          # If no results are returned, the email/password are incorrect, return forbidden code
                if isBrowser:
                    return redirect(url_for("index", msg="Sorry, we can't find those details! Check them and try again."))
                else:
                    return json.dumps({
                        "code": 403,
                        "msg": "Sorry, we can't find those details in the database! Check them and try again."
                    }), 403

            query.lastlogin = datetime.now()        # If it is found, update the lastlogin field
            db.session.commit()

            if isBrowser:
                resp = make_response(redirect(url_for('dash')))
            else:
                # Return the application key, application key id and bucket name for the connected B2
                # This is needed so that the cli client knows wassup
                resp = make_response(json.dumps({
                    "code": 200,
                    "msg": "You have been signed in",
                    "b2": {
                        "application_key_id": os.environ["APPLICATION_KEY_ID"],
                        "application_key": os.environ["APPLICATION_KEY"],
                        "bucket_name": os.environ["BUCKET_NAME"]
                    }
                }))

            resp.set_cookie("userid", str(query.userid))

            return resp
        except Exception as e:
            # print(e.with_traceback())
            print(e)

            if isBrowser:
                return redirect(url_for("index", msg="Something went wrong when trying to sign in"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when signing in"
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("index", msg="There was something wrong with the data you sent, try again!"))
        else:
            return json.dumps({
                "code": 400,
                "msg": "There was something wrong with the data you sent, please check and try again"
            })

