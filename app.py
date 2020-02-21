import io

from flask import Flask, request, render_template, url_for, redirect, send_file
from flask_heroku import Heroku

from src.api.comments.utils import getComments
from src.api.files.backblaze import B2Interface
from src.db import db

from src.api.signin.routes import signinBP
from src.api.signup.routes import signupBP
from src.api.groups.routes import groupsBP
from src.api.errors.routes import errorsBP
from src.api.email.routes import emailBP
from src.api.metadata.routes import metadataBP
from src.api.comments.routes import commentsBP
from src.api.files import filesBP

from src.api.files.file_create import newFile
from src.api.files.file_query import file_query
from src.api.groups.utils import getUserGroups, getGroupUsers, isGroupLeader
from src.api.user.utils import getUserData

import os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "bananas"

heroku = Heroku(app)
db.init_app(app)

app.register_blueprint(signinBP)
app.register_blueprint(signupBP)
app.register_blueprint(groupsBP)
app.register_blueprint(errorsBP)
app.register_blueprint(emailBP)
app.register_blueprint(filesBP)
app.register_blueprint(metadataBP)
app.register_blueprint(commentsBP)


APPLICATION_KEY_ID = os.environ['APPLICATION_KEY_ID']
APPLICATION_KEY = os.environ['APPLICATION_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']

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

    if id not in list(map(lambda x: str(x.groupid), groupData)):
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

    userGroups = getUserGroups(request.cookies.get("userid"))
    userData = getUserData(request.cookies.get("userid"))

    return render_template("newfile.html", userGroups=userGroups, user=userData)


@app.route("/file/<id>")
def file(id):
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    fileData = file_query({"fileid": id})[0]

    if not file:
        return redirect(url_for('dash', msg="Sorry, you do not have access to this file"))

    fileComments = getComments(id)
    userData = getUserData(request.cookies.get("userid"))
    isLeader = (True in [isGroupLeader(request.cookies.get("userid"),
                                       str(group["groupid"])) for group in fileData["groups"]]) or userData.admin

    return render_template("file.html", file=fileData, isLeader=isLeader, comments=fileComments)


@app.route("/version/<id>")
def version(id):
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    versionData = file_query({"versionid": id})[0]

    if not versionData:
        return redirect(url_for('dash', msg="Sorry, you do not have access to this file"))

    userData = getUserData(request.cookies.get("userid"))
    isLeader = (versionData['versions'][0]['author'] == userData)\
               or (True in [isGroupLeader(request.cookies.get("userid"), str(group["groupid"])) for group in versionData["groups"]])\
               or userData["admin"]

    return render_template("version.html", version=versionData, isLeader=isLeader)


@app.route('/download/<versionid>/<filename>', methods=['GET', 'POST'])
def download(versionid, filename):
    versionData = file_query({"versionid": versionid})[0]

    backblaze = B2Interface(application_key_id=os.environ.get("APPLICATION_KEY_ID"),
                            application_key=os.environ.get("APPLICATION_KEY"),
                            bucket_name=os.environ.get("BUCKET_NAME"))

    fileInfo = backblaze.downloadFileByVersionId(str(versionData["versions"][0]["versionid"]))
    return send_file(
        io.BytesIO(bytes(fileInfo["file_body"])),
        attachment_filename=versionData["filename"]
    )


@app.route("/bulkcomment")
def bulkCommentPage():
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    files = file_query({})

    return render_template("bulkcomment.html", files=files)

if __name__ == "main":
    app.run(threaded=True, port=5000)
