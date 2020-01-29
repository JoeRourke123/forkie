from flask import Flask, request, render_template, url_for, make_response, redirect
from flask_heroku import Heroku

import json

from src.db import db

from src.api.SigninAndSignup import signin, signup

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
    req = signin(db, request.form)

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
    req = signup(db, request.form)

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

if __name__ == "main":
    app.run(threaded=True, port=5000)
