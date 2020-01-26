from flask import Flask, request, render_template
from src.db import db, UserTable
from flask_heroku import Heroku
from time import time

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

heroku = Heroku(app)
db.init_app(app)

@app.route("/")
def index():
    return render_template("index.html")


# APIs
@app.route("/api/0.1/signup", methods=["POST"])
def signup():
    userData = UserTable({
        "username": request.form["username"],
        "email": request.form["email"],
        "password": request.form["password"], # Replace with hashed password eventually
        "lastlogin": time()
    }).__dict__

    try:
        db.session.add(userData)
        db.session.commit()
    except Exception as e:
        print("Failed Signup for user... " + request.form["email"])

    return "Sign up Complete!"


if __name__ == "main":
    app.run(threaded=True, port=5000)
