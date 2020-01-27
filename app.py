from flask import Flask, request, render_template, url_for, make_response
from src.db import db
from src.db.UserTable import UserTable
from src.db.GroupTable import GroupTable
from src.db.FileTable import FileTable
from src.db.FileVersionTable import FileVersionTable
from src.utils import result

from flask_heroku import Heroku

from datetime import datetime
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

heroku = Heroku(app)
db.init_app(app)


# Routes
@app.route("/")
def index():
    return render_template("index.html")


# APIs
@app.route("/api/0.1/signup", methods=["POST"])
def signup():
    userdata = UserTable.UserTable({            # Define an instance of the UserTable class with the entered data
        "username": request.form["username"],
        "email": request.form["email"],
        "password": request.form["password"],  # Replace with hashed password eventually
        "lastlogin": datetime.now()
    })

    try:
        db.session.add(userdata)                # Add the newly instantiated object to the DB
        db.session.commit()                     # Ensure the database transaction properly completes
    except Exception as e:
        print("Failed Signup for user... " + request.form["email"])
        print(e)
        sys.stdout.flush()                      # Output to Heroku log if an error occurs

        return result(500)                      # Return a 500 error code

    return result(200)                          # If successful, return a 200 code


@app.route("/api/0.1/signin", methods=["POST"])
def signin():
    if request.form["email"] or request.form["password"]:       # Server side check for user email and password entry
        try:
            query = UserTable.query.filter_by(email=request.form['email']).filter_by(password=request.form['password']).first()
            # Query the database with the entered email and password combination

            if not query:                   # If no results are returned, the email/password are incorrect
                return result(400)

            query.lastlogin = datetime.now()        # If it is found, update the lastlogin field
            db.session.commit()

            response = make_response(result(200, {      # Make a 200 accepted response containing the user's ID
                "userid": str(query.userid)
            }))
            response.set_cookie('userid', str(query.userid))    # Set the ID as a cookie also

            return response
        except Exception as e:
            print(e)
            sys.stdout.flush()
            return result(500)


if __name__ == "main":
    app.run(threaded=True, port=5000)
