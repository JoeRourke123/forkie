from flask import Flask, request, render_template, url_for, make_response
from src.db import db
from src.db.UserTable import UserTable
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
def index(msg=None):
    if request.cookies.get('userid'):
        return url_for('dashboard')

    return render_template("index.html", msg=msg)

@app.route("/dashboard")
def dashboard():
    data = {} # Will be collected from APIs on page call - will include user data (email, name and last logon), user groups (group name, group id), user files (filename, fileid)
    return render_template("dashboard.html", data=data)


# APIs
@app.route("/api/0.1/signup", methods=["POST"])
def signup():
    userdata = UserTable.UserTable({
        "username": request.form["username"],
        "email": request.form["email"],
        "password": request.form["password"], # Replace with hashed password eventually
        "lastlogin": datetime.now()
    })

    try:
        db.session.add(userdata)
        db.session.commit()
    except Exception as e:
        print("Failed Signup for user... " + request.form["email"])
        print(e)
        sys.stdout.flush()

        return result(500)

    return result(200)


@app.route("/api/0.1/signin", methods=["POST"])
def signin():
    if request.form["email"] or request.form["password"]:
        try:
            query = UserTable.query.filter_by(email=request.form['email']).filter_by(password=request.form['password']).first()

            query.lastlogin = datetime.now()
            db.session.commit()

            response = make_response(result(200, {
                "userid": str(query.userid)
            }))
            response.set_cookie('userID', str(query.userid))

            return response
        except Exception as e:
            return result(500)

    return result(400)

if __name__ == "main":
    app.run(threaded=True, port=5000)
