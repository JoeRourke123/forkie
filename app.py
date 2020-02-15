from flask import Flask, request, render_template, url_for, redirect, session
from flask_heroku import Heroku

from src.db import db

from src.api.signin.routes import signinBP
from src.api.signup.routes import signupBP
from src.api.files.file_query import fQueryBP as queryBP, file_query
from src.api.groups.routes import groupsBP
from src.api.errors.routes import errorsBP
from src.api.email.routes import emailBP
from src.api.files.file_create import filesBP

from src.api.groups.utils import getUserGroups, getGroupUsers, isGroupLeader, getGroupData
from src.api.user.utils import getUserData
from src.api.files.utils import getFileVersions, getFileGroups

import json

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "bananas"

heroku = Heroku(app)
db.init_app(app)

app.register_blueprint(signinBP)
app.register_blueprint(signupBP)
app.register_blueprint(queryBP)
app.register_blueprint(filesBP)
app.register_blueprint(groupsBP)
app.register_blueprint(errorsBP)
app.register_blueprint(emailBP)


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
    groupData = getUserGroups(request.cookies.get("userid"))
    files = file_query({})

    if not userData:
        return redirect(url_for('error.error', code=401))

    return render_template("dashboard.html", user=userData, groups=groupData, files=files)


@app.route("/group/<id>")
def group(id):
    groupData = getUserGroups(request.cookies.get("userid"))
    groupUsers = getGroupUsers(id)
    groupFiles = file_query({"groupid": id})
    isLeader = isGroupLeader(request.cookies.get("userid"), id)

    if not request.cookies.get('userid'):
        return redirect(url_for('index', msg="Please sign in to see your dashboard"))
    elif id not in list(map(lambda x: str(x.groupid), groupData)):
        return redirect(url_for('dash', msg="You do not have permissions to view this group"))

    return render_template("group.html",
                           user=getUserData(request.cookies.get("userid")),
                           groupData=list(filter(lambda x: str(x.groupid) == id, groupData))[0],
                           groupUsers=groupUsers, isLeader=isLeader,
                           groupFiles=groupFiles)


@app.route("/group/new")
def newGroupPage():
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page"))

    return render_template("newgroup.html")


@app.route("/file/new")
def newFilePage():
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page"))

    print(request.referrer)
    userGroups = getUserGroups(request.cookies.get("userid"))
    userData = getUserData(request.cookies.get("userid"))

    return render_template("newfile.html", userGroups=userGroups, user=userData)


@app.route("/file/<id>")
def file(id):
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    fileData = file_query({"fileid": id})

    if not file:
        return redirect(url_for('dash', msg="Sorry, you do not have access to this file"))

    return render_template("file.html", file=fileData)


if __name__ == "main":
    app.run(threaded=True, port=5000)
