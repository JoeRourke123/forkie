from flask import current_app as app
from flask import render_template, Blueprint, request, make_response, redirect, url_for

from src.api.user.func import getUserGroups
from src.db.FileTable import FileTable
from src.db.FileVersionTable import FileVersionTable
from src.db.FileGroupTable import FileGroupTable
from src.utils import hashPassword
from src.db import db

from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

### IGNORE THIS FILE I'M NOT FINISHED

### Create JSON SCHEMA FOR CREATING FILES

fCreateBP = Blueprint('signup', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api')


@fCreateBP.route("/signup", methods=["POST"])
def signup():
    isBrowser = bool(request.form is not None)
    data = request.form if isBrowser else request.json
    
    # If there is no userid inside the cookie from a cli user then return 401 (unauthorized error)
    if "userid" not in request.cookies and not isBrowser:
        return json.dumps({
            "code": 401,
            "msg": "Unauthorized. Make sure you sure you have logged in."
        })
    
    # Create data inside filetable
    filedata = FileTable({
        "filename": data["username"]
    })
    
    # Create
    fileversiondata = FileVersionTable({
        "fileid": data["fileid"],
        "extension": data["extension"],
        "versionhash": data["versionhash"]
    })