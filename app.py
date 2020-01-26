from flask import Flask, request, render_template
from src.db import db, UserTable
from flask_heroku import Heroku
from time import time

import sys

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
    userdata = UserTable.UserTable({
        "userid": "@7bj?U!z5+QHD@Y8n2g@uwTbYMMD3?!^G#pCY*?t!F5mMzxvH?BG3dg%hejVAx=58X6xMt6PdCbc+7@Sg34?^zM-eX*Gz+Tgh9n_NaVL%=eV2s?Qfy3u&yVWvkw&=KB&",
        "username": request.form["username"],
        "email": request.form["email"],
        "password": request.form["password"], # Replace with hashed password eventually
        "lastlogin": time()
    })

    try:
        db.session.add(userdata)
        db.session.commit()
    except Exception as e:
        print("Failed Signup for user... " + request.form["email"])
        print(e)
        sys.stdout.flush()

    return "Sign up Complete!"


if __name__ == "main":
    app.run(threaded=True, port=5000)
