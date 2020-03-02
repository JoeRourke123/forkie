import io
from datetime import datetime

from flask import Flask, request, render_template, url_for, redirect, send_file, session
from flask_heroku import Heroku

from src.api.comments.utils import getComments, getUnreadComments, readUnreadComments
from src.api.files.backblaze import B2Interface
from src.api.files.utils import leaderCheck
from src.db import db

from src.api.signin.routes import signinBP
from src.api.signup.routes import signupBP
from src.api.groups.routes import groupsBP
from src.api.email.routes import emailBP
from src.api.metadata.routes import metadataBP
from src.api.comments.routes import commentsBP
from src.api.files import filesBP

from src.api.files.file_query import file_query
from src.api.files.file_create import newFile       # Must be imported, despite not being used so the endpoint can be added to the Blueprint
from src.api.groups.utils import getUserGroups, getGroupData
from src.api.user.utils import getUserData

import os

from src.db.UserTable import UserTable

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "bananas"

heroku = Heroku(app)
db.init_app(app)

# Adds all the modular blueprint API routes to the app
app.register_blueprint(signinBP)
app.register_blueprint(signupBP)
app.register_blueprint(groupsBP)
app.register_blueprint(emailBP)
app.register_blueprint(filesBP)
app.register_blueprint(metadataBP)
app.register_blueprint(commentsBP)

APPLICATION_KEY_ID = os.environ['APPLICATION_KEY_ID']
APPLICATION_KEY = os.environ['APPLICATION_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']


# Runs before every request to check whether this is a new session and to alter the lastlogin field in the user's database entry
@app.before_request
def beforeRequest():
    if request.cookies.get("userid") and not session.get("active"):
        session["active"] = True                                    # Set a temporary session active variable to true when the
                                                                    # user starts a session, and will expire in ~30 minutes if not reaccessed
        userRow = UserTable.query.get(request.cookies.get("userid"))

        session["lastlogin"] = userRow.lastlogin

        userRow.lastlogin = datetime.now()      # Change the user's lastlogin to current time object
        db.session.commit()                     # Commits these changes to the database


# Routes
@app.route("/")
def index(msg=None, code=200):
    if request.cookies.get('userid'):       # If the user is signed in, it redirects them to the dashboard page
        return redirect(url_for('dash'))

    return render_template("index.html", code=code, msg=msg)


@app.route("/dash")
def dash():
    if not request.cookies.get('userid'):   # Repeated for every route, checks if the user is signed / has a userid in the coookies
        return redirect(url_for('index', msg="Please sign in to see your dashboard"))   # Redirects them if it doesn't exist

    userData = getUserData(request.cookies.get("userid"))           # Gets dictionary of the user's usertable data
    groupData = getUserGroups(request.cookies.get("userid"))        # Get all the user's groups in order to show them in the dropdown
    files = file_query({})                                          # Retrieve all user's files in order to show in file list
    unread = getUnreadComments(files, request.cookies.get("userid"))    # Gets any unread comments, to display in the notifications pane

    return render_template("dashboard.html", user=userData, groups=groupData, files=files, unreadComments=unread)


# Route displaying all the data concerning a group, given its id
@app.route("/group/<id>")
def group(id : str):
    groupData = getGroupData(id)      # Returns a dictionary of all accessible group data (files, members, name, id etc)
    userData = getUserData(request.cookies.get("userid"))   # Returns the basic user data stored in the usertable

    if not request.cookies.get('userid'):
        return redirect(url_for('index', msg="Please sign in to see your dashboard"))

    if not groupData or (userData not in groupData["members"] and not userData["admin"]):   # If the user isn't in the group
        return redirect(url_for('dash', msg="You do not have permissions to view this group"))

    return render_template("group.html",
                           user=userData,
                           group=groupData,
                           isLeader=groupData["groupleader"]["userid"] == userData["userid"])


# Route containing the form to create a new group
@app.route("/group/new")
def newGroupPage():
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page"))

    return render_template("newgroup.html")


# Route containing a form for new file creation
@app.route("/file/new")
def newFilePage():
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page"))

    userGroups = getUserGroups(request.cookies.get("userid"))
    userData = getUserData(request.cookies.get("userid"))

    return render_template("newfile.html", userGroups=userGroups, user=userData)


# Route showing all the data about files, such as versions, groups, comments - and allows admins to run actions on the file
@app.route("/file/<id>")
def file(id : str):
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    fileData = file_query({"fileid": id})   # Gets list of files associated with file id provided in url, although should only be one

    if not fileData:        # Checks if any file is returned from the file query
        return redirect(url_for('dash', msg="Sorry, you do not have access to this file"))
    else:
        fileData = fileData[0]      # Should only be one, so fetches the first index

    userData = getUserData(request.cookies.get("userid"))
    userGroups = getUserGroups(userData["userid"])      # Gets groups in order for admins to give other group's file access

    isLeader = leaderCheck(fileData["groups"], userData["userid"]) or userData["admin"]

    readUnreadComments(id, userData["userid"])      # Marks any comment in the file that isn't read as read
    fileComments = getComments(id)                  # Fetches the files comments, with all of them read by current user

    return render_template("file.html", file=fileData, isLeader=isLeader,
                           comments=fileComments, userGroups=userGroups, archive=False)


# Displays the archive page, only accessible to admins
@app.route("/archive")
def archive():
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    userData = getUserData(request.cookies.get("userid"))       # Gets user data to check whether it is admin

    if not userData["admin"]:
        return redirect(url_for("dash", msg="You don't have permission to see this page"))

    files = file_query({"archived": True})      # Fetches all files with any archived file versions

    return render_template("archive.html", files=files)


# Shows a slightly altered file page for the archived version of a file
@app.route("/archive/file/<id>")
def archivedFile(id : str):
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    file = file_query({"fileid": id, "archived": True})

    if not file:
        return redirect(url_for('dash', msg="Sorry, you do not have access to this file"))


    userGroups = getUserGroups(request.cookies.get("userid"))
    fileComments = getComments(id)                  # Fetches the files comments, with all of them read by current user

    return render_template("file.html", file=file[0], isLeader=True, userGroups=userGroups, comments=fileComments, archive=True)


# Page showing file version details.
@app.route("/version/<id>")
def version(id: str):
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    versionData = file_query({"versionid": id})[0]          # Query the file associated with the passed file version

    if not versionData:                                     # If the file version cannot be found, or the user doesn't have access
        return redirect(url_for('dash', msg="Sorry, you do not have access to this file"))

    userData = getUserData(request.cookies.get("userid"))   # Gets the users Data to check whether they have leader/admin/creator access
    isLeader = (versionData['versions'][id]['author'] == userData)\
               or leaderCheck(versionData["groups"], userData["userid"]) \
               or userData["admin"]

    return render_template("version.html", id=id, version=versionData, isLeader=isLeader)


# Page to retrieve a file's contents so it can be fetched from a download link
@app.route('/download/<id>', methods=['GET', 'POST'])
def download(id : str):
    versionData = file_query({"versionid": id})[0]          # Retrieve the file data with the version id using the file_query method

    backblaze = B2Interface(application_key_id=APPLICATION_KEY_ID,
                            application_key=APPLICATION_KEY,
                            bucket_name=BUCKET_NAME)      # Define an instance of the B2Interface in order to communicate
                                                                            # with the Backblaze bucket

    fileInfo = backblaze.downloadFileByVersionId(str(versionData["versions"][0]["versionid"]))  # Downloads the file from the bucket
    return send_file(                                                                           # Uses Flask's send_file function in order
        io.BytesIO(bytes(fileInfo["file_body"])),                                               # serve the file in a readable format for
        attachment_filename=versionData["filename"]                                             # the browser
    )


@app.route("/bulkcomment")
def bulkCommentPage():
    if not request.cookies.get("userid"):
        return redirect(url_for('index', msg="You are not signed in, please sign in to see this page."))

    files = file_query({})      # Empty query fetches all the files accessible to a user

    return render_template("bulkcomment.html", files=files)

if __name__ == "main":
    app.run(threaded=True, port=4000)
