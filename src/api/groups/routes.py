from flask import current_app as app
from flask import render_template, Blueprint, request, redirect, url_for

import json

from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db import db

groupsBP = Blueprint('groups', __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/groups')


@groupsBP.route("/new", methods=["POST"])
def newGroup():
    isBrowser = request.cookies.get("client") == "browser"
    data = request.form if isBrowser else request.json

    if request.cookies.get("userid"):
        group = GroupTable({
            "groupName": data.get("name"),
            "groupLeader": request.cookies.get("userid")
        })

        usergroup = UserGroupTable(group.groupid, request.cookies.get("user"))

        try:
            db.session.add(group)
            db.session.add(usergroup)
            db.session.commit()
        except Exception as e:
            if isBrowser:
                return redirect(url_for('errors.error', code=500))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when creating your group"
                }), 500
    else:
        if isBrowser:
            return redirect(url_for('errors.error', code=403))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this"
            }), 403

    if isBrowser:
        return redirect(url_for('groups.viewGroup'))
    else:
        return json.dumps({
            "code": 200,
            "msg": "Your group has been created"
        })