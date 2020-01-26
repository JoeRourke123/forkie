from flask import Flask, request, render_template, url_for
from src.db import db
from src.db.UserTable import UserTable
from flask_heroku import Heroku

from datetime import datetime
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

heroku = Heroku(app)
db.init_app(app)

@app.route("/")
def index(msg=None):
    return render_template("index.html", msg=msg)


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

    return "Sign up Complete!"


@app.route("/api/0.1/signin", methods=["POST"])
def signin():
    if request.form["email"] or request.form["password"]:
        query = UserTable.query.filter_by(email=request.form['email']).filter_by(password=request.form['password']).first()

        return str(query)

    return url_for('index', msg="Please enter a username and password")

if __name__ == "main":
    app.run(threaded=True, port=5000)
