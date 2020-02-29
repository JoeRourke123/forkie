from flask import current_app as app
from flask import render_template, Blueprint, request, make_response, redirect, url_for

from src.db.UserTable import UserTable
from src.db import db

from hashlib import sha256
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

signupBP = Blueprint('signup', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api')



def hashPassword(password):
    """ Given a password (or any text input) will return a sha256 hash of the text
        - password: the user inputted plain text password to hash

        - returns: a string hex representation of the sha256 hashed string
    """

    return str(sha256(password.encode('utf-8')).hexdigest())

@signupBP.route("/signup", methods=["POST"])
def signup():
    """ Endpoint to remove a user from a specific group - same endpoint to allow user to leave a group

        - email: the user inputted email, in order to send notification emails to the user
        - username: the user's display name / real name to allow for personalised messages
        - password: the password of the user's account

        - returns: a response for the client to interpret based on the success of the operation
    """

    isBrowser = bool("email" in request.form)
    data = request.form if isBrowser else json.loads(request.data)

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
            return redirect(url_for('index', msg="That email is already associated with an account!"))
        else:
            return json.dumps({
                "msg": "That email is already assoicated with an account!"
            }), 401
    except Exception as e:
        if isBrowser:
            return redirect(url_for("index", msg="Something went wrong when creating an account!"))
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
