from flask import Blueprint, request, redirect, url_for

import json
from traceback import print_exc
import uuid

from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db import db

groupsBP = Blueprint('groups', __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/groups')


@groupsBP.route("/new", methods=["POST"])
def newGroup():
    isBrowser = "groupName" in request.form
    data = request.form if isBrowser else request.data

    if request.cookies.get("userid"):
        try:
            group = GroupTable({
                "groupname": data.get("groupName"),
                "groupleaderid": request.cookies.get("userid")
            })
            db.session.add(group)
            db.session.commit()

            usergroup = UserGroupTable({
                "groupid": str(group.groupid),
                "userid": request.cookies.get("userid")
            })
            db.session.add(usergroup)
            db.session.commit()
        except Exception as e:
            return str(e)

            if isBrowser:
                return redirect(url_for('errors.error', code=500, msg=print_exc()))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when creating your group"
                }), 500
    else:
        if isBrowser:
            return redirect(url_for('errors.error', code=403, msg=print_exc()))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
                "exc": print_exc()
            }), 403

    if isBrowser:
        return redirect(url_for('group', id=group.groupid))
    else:
        return json.dumps({
            "code": 200,
            "msg": "Your group has been created"
        })