from flask import Blueprint, request, redirect, url_for, make_response

import json
from traceback import print_exc
from sqlalchemy import and_

from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db.UserTable import UserTable

from src.db import db

from src.api.user.utils import getUserData
from src.api.groups.utils import getUserGroups

groupsBP = Blueprint('groups', __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/groups')


@groupsBP.route("/addMember", methods=["POST"])
def addMember():
    """ Endpoint to add a user to a specified group

        - groupid: the UUID of the group in which the new member will be added to
        - userid: the UUID of the user who triggered the group member addition
        - email: the email address of the user to add to the group

        - returns: a response for the client to interpret based on the success of the operation
    """

    isBrowser = "email" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if request.cookies.get("userid"):
        try:
            group = GroupTable.query.filter(and_(GroupTable.groupleaderid==request.cookies.get("userid"), GroupTable.groupid==data["groupid"])).first()

            if not group:  # If a group where the current user is the leader and the id is the one supplied is not found
                if isBrowser:   # The user must not have leader permissions and must be redirected
                    return redirect(url_for('dash', msg="Sorry you are not permitted to complete this action"))
                else:
                    return json.dumps({
                        "code": 401,
                        "msg": "You don't have permission to complete this action!"
                    }), 401

            # Get the user data from the inputted user email
            newUserData = UserTable.query.filter_by(email=data["email"]).first()

            # If there isn't a user with that email
            if not newUserData:
                return redirect(url_for('group', id=group.groupid, msg="Sorry, we couldn't find that user!"))

            # Otherwise add them to the user-group linking table
            usergroup = UserGroupTable({
                "groupid": group.groupid,
                "userid": newUserData.userid
            })
            db.session.add(usergroup)
            db.session.commit()

            # Inform the user that the action was successful
            if isBrowser:
                return redirect(url_for('group', id=group.groupid, msg=newUserData.username + " has been added to " + group.groupname))
            else:
                return json.dumps({
                    "code": 200,
                    "msg": "User has been added!",
                })
        except Exception as e:
            print(print_exc())

            if isBrowser:
                return redirect(url_for("group", id=data["groupid"], msg="Something went wrong when adding member"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when adding the user."
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
                "exc": print_exc()
            }), 403


@groupsBP.route("/removeMember", methods=["POST"])
def removeMember():
    """ Endpoint to remove a user from a specific group - same endpoint to allow user to leave a group

        - groupid: the UUID of the group in which the file will become associated with
        - userid (cookie): the UUID of the user who triggered the member removal, in a cookie
        - userid: UUID of the user who should be removed from the group, in the form data

        - returns: a response for the client to interpret based on the success of the operation
    """

    isBrowser = "userid" in request.form    # Checks if the request is coming from the browser or the CLI
    data = request.form if isBrowser else json.loads(request.data)

    if request.cookies.get("userid"):
        try:                            # Fetch the group data from the provided groupid
            group = GroupTable.query.filter_by(groupid=data["groupid"]).first()

            # Checks the group exists, and that either the user is the leader OR they are attempting to remove themselves (i.e: leaving the group)
            if not group or not (str(group.groupleaderid) is not request.cookies.get("userid") and request.cookies.get("userid") is not data["userid"]):
                if isBrowser:
                    return redirect(url_for('dash', msg="Sorry you are not permitted to complete this action"))
                else:
                    return json.dumps({
                        "code": 401,
                        "msg": "You don't have permission to complete this action!"
                    }), 401

            # Finds the record associated with the user in the UserGroupTable
            usergroup = UserGroupTable.query.filter(and_(UserGroupTable.userid==data["userid"], UserGroupTable.groupid==data["groupid"])).first()
            db.session.delete(usergroup)        # Deletes the record
            db.session.commit()

            # Different responses depending on if the user has removed themselves, or another user
            if data["userid"] == request.cookies.get("userid"):
                if isBrowser:
                    return redirect(url_for('dash', msg="You have left " + group.groupname))
                else:
                    return json.dumps({
                        "code": 200,
                        "msg": "You have left " + group.groupname,
                    })
            else:
                if isBrowser:
                    return redirect(url_for('group', id=group.groupid, msg="User has been removed from " + group.groupname))
                else:
                    return json.dumps({
                        "code": 200,
                        "msg": "Your group has been renamed"
                    })
        except Exception as e:
            print(print_exc())

            if isBrowser:
                return redirect(url_for("group", id=data["groupid"], msg="Something went wrong when removing user"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when removing the user."
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
            }), 403


@groupsBP.route("/new", methods=["POST"])
def newGroup():
    """ Endpoint to create a new group

        - groupname: the user-inputted name of the group to be created
        - userid: UUID of the user creating the group, so they can be set to the groupleader

        - returns: a response for the client to interpret based on the success of the operation
    """

    isBrowser = "groupname" in request.form                 # Check for which platform request is coming from
    data = request.form if isBrowser else json.loads(request.data)

    if request.cookies.get("userid"):
        try:
            group = GroupTable({                            # Creates a record in the GroupTable with the provided data
                "groupname": data.get("groupname"),
                "groupleaderid": request.cookies.get("userid")
            })
            db.session.add(group)                           # Adds the group to allow foreign key constraints
            db.session.commit()

            usergroup = UserGroupTable({                    # Creates a UserGroup record for the current user
                "groupid": str(group.groupid),
                "userid": request.cookies.get("userid")
            })
            db.session.add(usergroup)
            db.session.commit()
        except Exception as e:
            print(print_exc())                              #

            if isBrowser:
                return redirect(url_for("dash", msg="Something went wrong when creating your group"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when creating your group"
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
                "exc": print_exc()
            }), 403

    if isBrowser:
        return redirect(url_for("group", id=group.groupid))
    else:
        return json.dumps({
            "code": 200,
            "msg": "Your group has been created"
        })


@groupsBP.route("/rename", methods=["POST"])
def renameGroup():
    """ Endpoint to rename a specified group

        - groupid: the UUID of the group to rename
        - userid (cookie): the UUID of the user who triggered the rename, and to check they have correct permissions
        - newname: string of the name to which the specified group should be changed to

        - returns: a response for the client to interpret based on the success of the operation
    """

    isBrowser = "groupid" in request.form
    data = request.form if isBrowser else request.data

    if request.cookies.get("userid"):
        try:
            group = GroupTable.query.filter(and_(GroupTable.groupleaderid==request.cookies.get("userid"),
                                                 GroupTable.groupid==data["groupid"])).first()

            if not group and not getUserData(request.cookies.get("userid")).admin:
                if isBrowser:
                    return redirect(url_for('dash', msg="Sorry you are not permitted to complete this action"))
                else:
                    return json.dumps({
                        "code": 401,
                        "msg": "You don't have permission to complete this action!"
                    }), 401

            group.groupname = data["newname"]

            db.session.commit()

        except Exception as e:
            if isBrowser:
                return redirect(url_for("group", id=data["groupid"], msg="Something went wrong when renaming your group"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when renaming your group"
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
            }), 403

    if isBrowser:
        return redirect(url_for('group', id=group.groupid, msg="Group successfully renamed"))
    else:
        return json.dumps({
            "code": 200,
            "msg": "Your group has been renamed"
        })


@groupsBP.route("/delete", methods=["POST"])
def deleteGroup():
    """ Endpoint to delete a group, and all data associated with it

        - groupid: the UUID of the group to delete
        - userid: the UUID of the user who triggered the deletion, to check permissions

        - returns: a response for the client to interpret based on the success of the operation
    """

    isBrowser = "groupid" in request.form
    data = request.form if isBrowser else request.data

    if request.cookies.get("userid"):
        try:
            group = GroupTable.query.filter(and_(GroupTable.groupid==data["groupid"],
                                                 GroupTable.groupleaderid==request.cookies.get("userid"))).first()

            # Checks whether user is a groupleader or if they are an admin
            if not group and not getUserData(request.cookies.get("userid"))["admin"]:
                if isBrowser:
                    return redirect(url_for('dash', msg="Sorry you are not permitted to complete this action"))
                else:
                    return json.dumps({
                        "code": 401,
                        "msg": "You don't have permission to complete this action!"
                    }), 401

            db.session.delete(group)    # Delete record and commit the changes
            db.session.commit()

            return redirect(url_for('dash', msg=group.groupname + " has been deleted"))
        except Exception as e:
            print(print_exc())

            if isBrowser:
                return redirect(url_for("group", id=data["groupid"], msg="Something went wrong when deleting your group"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when removing the user."
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("index", msg="You need to be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
                "exc": print_exc()
            }), 403
