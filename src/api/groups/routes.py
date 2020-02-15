from flask import Blueprint, request, redirect, url_for

import json
from traceback import print_exc
from sqlalchemy import and_

from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db.UserTable import UserTable

from src.db import db

from src.api.user.utils import getUserData

groupsBP = Blueprint('groups', __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/groups')


@groupsBP.route("/addMember", methods=["POST"])
def addMember():
    isBrowser = "email" in request.form
    data = request.form if isBrowser else request.data

    if request.cookies.get("userid"):
        try:
            group = GroupTable.query.filter(and_(GroupTable.groupleaderid==request.cookies.get("userid"), GroupTable.groupid==data["groupid"])).first()

            if not group:
                return redirect(url_for('dash', msg="Sorry you are not permitted to complete this action"))

            newUserData = UserTable.query.filter_by(email=data["email"]).first()

            if not newUserData:
                return redirect(url_for('group', id=group.groupid, msg="Sorry, we couldn't find that user!"))

            usergroup = UserGroupTable({
                "groupid": group.groupid,
                "userid": newUserData.userid
            })
            db.session.add(usergroup)
            db.session.commit()

            return redirect(url_for('group', id=group.groupid, msg=newUserData.username + " has been added to " + group.groupname))

        except Exception as e:
            print(print_exc())
            return str(e)

            if isBrowser:
                return redirect(url_for('errors.error', code=500, msg=print_exc()))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when adding the user."
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


@groupsBP.route("/removeMember", methods=["POST"])
def removeMember():
    isBrowser = "userid" in request.form
    data = request.form if isBrowser else request.data

    if request.cookies.get("userid"):
        try:
            print(data)
            group = GroupTable.query.filter_by(groupid=data["groupid"]).first()

            if not group or not (str(group.groupleaderid) is not request.cookies.get("userid") and request.cookies.get("userid") is not data["userid"]):
                return redirect(url_for('dash', msg="Sorry you are not permitted to complete this action"))

            usergroup = UserGroupTable.query.filter(and_(UserGroupTable.userid==data["userid"], UserGroupTable.groupid==data["groupid"])).first()
            db.session.delete(usergroup)
            db.session.commit()

            return redirect(url_for('group', id=group.groupid, msg="User has been removed from " + group.groupname))
        except Exception as e:
            print(print_exc())
            return str(e)

            if isBrowser:
                return redirect(url_for('errors.error', code=500, msg=print_exc()))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when removing the user."
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


@groupsBP.route("/new", methods=["POST"])
def newGroup():
    isBrowser = "groupname" in request.form
    data = request.form if isBrowser else request.data

    if request.cookies.get("userid"):
        try:
            group = GroupTable({
                "groupname": data.get("groupname"),
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


@groupsBP.route("/rename", methods=["POST"])
def renameGroup():
    isBrowser = "groupid" in request.form
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