from flask import Flask, request, render_template, url_for, make_response, redirect
from flask_heroku import Heroku

from datetime import datetime
import sys
import json

from sqlalchemy.exc import IntegrityError


from src.db import db
from src.db.UserTable import UserTable


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

heroku = Heroku(app)
db.init_app(app)


# Routes
@app.route("/")
def index(msg=None):
    if request.cookies.get('userid'):
        return redirect(url_for('dashboard'))

    return render_template("index.html", msg=msg)


@app.route("/dash")
def dashboard():
    if not request.cookies.get('userid'):
        return redirect(url_for('index', msg="Please sign in to see your dashboard"))

    return render_template("dashboard.html")


# Web Endpoints
@app.route("/api/web/signin", methods=["POST"])
def webSignin():
    req = signin(request.form)

    if req['result'] == 200:
        resp = make_response(redirect(url_for('dashboard')))
        resp.set_cookie('userid', req['userid'])
        return resp
    elif req['result'] == 400:
        return redirect(url_for('index', msg="Sorry, we don't recognise that email/password combination"))
    elif req['result'] == 500:
        return redirect(url_for('index', msg="It appears an error has occured. Please try again"))


@app.route("/api/web/signup", methods=["POST"])
def webSignup():
    req = signup(request.form)

    if req['result'] == 200:
        return redirect(url_for('index', msg="Account created. You can now signin!"))
    elif req['result'] == 500:
        return redirect(url_for('index', msg="Sorry, something went wrong. Please try again!"))
    elif req['result'] == 400:
        return redirect(url_for('index', msg="That email is already in use, do you want to sign in?"))


# CLI Endpoints
@app.route("/api/cli/signup", methods=["POST"])
def apiSignup():
    return json.dumps(signup(request.json))

@app.route("/api/cli/signin", methods=["POST"])
def apiSignin():
    return json.dumps(signin(request.json))         # Always use json.dumps when returning JSON values
                                                    # Routes must return strings

# Sign in/up functions
def signin(data):
    if data["email"] or data["password"]:       # Server side check for user email and password entry
        try:
            query = UserTable.query.filter_by(email=data['email']).filter_by(password=data['password']).first()
            # Query the database with the entered email and password combination

            if not query:                   # If no results are returned, the email/password are incorrect, return forbidden code
                return {
                    "result": 400
                }

            query.lastlogin = datetime.now()        # If it is found, update the lastlogin field
            db.session.commit()

            return {
                "result": 200,
                "userid": str(query.userid)
            }
        except Exception as e:
            print(e)
            sys.stdout.flush()
            return {
                "result": 500
            }


def signup(data):
    userdata = UserTable({  # Define an instance of the UserTable class with the entered data
        "username": data["username"],
        "email": data["email"],
        "password": data["password"],  # Replace with hashed password eventually
        "lastlogin": datetime.now()
    })

    try:
        db.session.add(userdata)  # Add the newly instantiated object to the DB
        db.session.commit()  # Ensure the database transaction properly completes
    except IntegrityError as e:  # Thrown if the user attempts to use an email that already exists in the table
        return {
            "result": 400,
        }
    except Exception as e:
        print("Failed Signup for user... " + data["email"])
        print(e)
        sys.stdout.flush()  # Output to Heroku log if an error occurs

        return {
            "result": 500
        }  # Return a 500 error code

    return {
        "result": 200
    }  # If successful, return a 200 code


if __name__ == "main":
    app.run(threaded=True, port=5000)
