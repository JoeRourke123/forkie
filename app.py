from flask import Flask, request, render_template, url_for, redirect, session
from flask_heroku import Heroku

from src.db import db

from src.api.signin.routes import signinBP
from src.api.signup.routes import signupBP
from src.api.groups.routes import groupsBP
from src.api.errors.routes import errorsBP

from src.api.user.func import getUserData

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "bananas"

heroku = Heroku(app)
db.init_app(app)

app.register_blueprint(signinBP)
app.register_blueprint(signupBP)
app.register_blueprint(groupsBP)
app.register_blueprint(errorsBP)


# Routes
@app.route("/")
def index(msg=None, code=200):
    if request.cookies.get('userid'):
        return redirect(url_for('dash'))

    return render_template("index.html", code=code, msg=msg)


@app.route("/dash")
def dash():

    if not request.cookies.get('userid'):
        return redirect(url_for('index', msg="Please sign in to see your dashboard"))

    userData = getUserData(request.cookies.get("userid"))

    if not userData:
        return redirect(url_for('error.error', code=401))

    return render_template("dashboard.html", user=userData)


if __name__ == "main":
    app.run(threaded=True, port=5000)
