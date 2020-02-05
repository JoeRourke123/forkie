from flask import current_app as app
from flask import render_template, Blueprint, request, make_response, redirect, url_for

from src.db.UserTable import UserTable
from src.utils import hashPassword
from app import db

from datetime import datetime
import json

signinBP = Blueprint('signin', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api')


@signinBP.route("/signin")
def signin():
    isBrowser = request.form.get("client") == "browser"

    data = request.form if isBrowser else request.json

    if data["email"] and data["password"]:       # Server side check for user email and password entry
        try:
            query = UserTable.query.filter_by(email=data['email'])\
                .filter_by(password=hashPassword(data['password'])).first()
            # Query the database with the entered email and password combination

            if not query:                           # If no results are returned, the email/password are incorrect, return forbidden code
                if isBrowser:
                    return redirect(url_for("signin.signin", code=403, msg="Sorry, we can't find those details in the database! Check them and try again."))
                else:
                    return json.dumps({
                        "code": 403,
                        "msg": "Sorry, we can't find those details in the database! Check them and try again."
                    }), 403

            query.lastlogin = datetime.now()        # If it is found, update the lastlogin field
            db.session.commit()

            if isBrowser:
                resp = make_response(redirect(url_for('dash.dash')))
            else:
                resp = make_response(json.dumps({"code": 200, "msg": "You have been signed in"}))

            resp.set_cookie("userid", query.userid)
            resp.set_cookie("client", "browser" if isBrowser else "cli")

            return resp
        except Exception as e:
            if isBrowser:
                return redirect(url_for("error.error", code=500, url="signin.signin"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when signing in"
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("error.error", code=400, url="signin.signin"))
        else:
            return json.dumps({
                "code": 400,
                "msg": "There was something wrong with the data you sent, please check and try again"
            })
