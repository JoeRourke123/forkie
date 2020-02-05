from flask import current_app as app
from flask import render_template, Blueprint, request, make_response, redirect, url_for

from src.db.UserTable import UserTable
from src.utils import hashPassword
from app import db

from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

signupBP = Blueprint('signup', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api')


@signupBP.route("/signup", methods=["POST"])
def signup():
    isBrowser = bool(request.form is not None)
    data = request.form if isBrowser else request.json

    userdata = UserTable({  # Define an instance of the UserTable class with the entered data
        "username": data["username"],
        "email": data["email"],
        "password": hashPassword(data["password"]),  # Replace with hashed password eventually
        "lastlogin": datetime.now()
    })

    try:
        db.session.add(userdata)  # Add the newly instantiated object to the DB
        db.session.commit()  # Ensure the database transaction properly completes
    except IntegrityError as e:  # Thrown if the user attempts to use an email that already exists in the table
        if isBrowser:
            return redirect(url_for('index', code=401, msg="That email is already associated with an account, try signing in!"))
        else:
            return json.dumps({
                "code": 401,
                "msg": "That email is already assoicated with an account, try signing in!"
            }), 401
    except Exception as e:
        if isBrowser:
            return redirect(url_for("error.error", code=500))
        else:
            return json.dumps({
                "code": 500,
                "msg": "Something has gone wrong"
            }), 500

    if isBrowser:
        return redirect(url_for('index', code=200, msg="Account created! You may now signin"))
    else:
        return json.dumps({
            "code": 200,
            "msg": "Your account has been created, you may not signin"
        })
