from flask import current_app as app
from flask import render_template, Blueprint, request, make_response, redirect, url_for

from src.db.UserTable import UserTable
from src.utils import hashPassword
from src.db import db

from datetime import datetime
import json

signinBP = Blueprint('signin', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api')


@signinBP.route("/signin", methods=["POST"])
def signin():
    print("First line")
    isBrowser = bool(request.form is not None)
    print("Gets here")
    data = request.form if isBrowser else request.json
    print("Gets here too")

    if data.get("email") and data.get("password"):       # Server side check for user email and password entry
        try:
            query = UserTable.query.filter_by(email=data['email'])\
                .filter_by(password=hashPassword(data['password'])).first()
            # Query the database with the entered email and password combination

            if not query:                           # If no results are returned, the email/password are incorrect, return forbidden code
                if isBrowser:
                    return redirect(url_for("index", code=403, msg="Sorry, we can't find those details in the database! Check them and try again."))
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
                resp = make_response(json.dumps({"code": 200, "msg": "You have been signed in"}))

            resp.set_cookie("userid", str(query.userid))
            resp.set_cookie("client", "browser" if isBrowser else "cli")

            return resp
        except Exception as e:
            print(e.with_traceback())

            if isBrowser:
                return redirect(url_for("errors.error", code=500, url="signin.signin"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when signing in"
                }), 500
    else:
        print(isBrowser)
        print(request.data)
        print(request.form)
        print(request.args)

        if isBrowser:
            return redirect(url_for("errors.error", code=400, url="signin.signin"))
        else:
            return json.dumps({
                "code": 400,
                "msg": "There was something wrong with the data you sent, please check and try again"
            })

