from flask import Blueprint, request, redirect, url_for

import json
from traceback import print_exc

from src.api.user.utils import getUserData
from src.api.groups.utils import getGroupUsers
from src.api.email.utils import sendGroupEmail

# Email blueprint to modularise the email related endpoints away from the main app routes
emailBP = Blueprint('email', __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/email')


@emailBP.route("/group", methods=["POST"])
def emailGroup():
    """ POST Endpoint for sending the users in a group an email.
        - groupid: the UUID of the group to send the email to
        - userid: accessed from the user cookie, indicates the sender of the email
        - subject: the subject header of the email being sent
        - content: the content to include in the requested email body

        - returns: a success response/redirection if the email sends successfully, or a error response otherwise
    """

    isBrowser = "groupid" in request.form
    data = request.form if isBrowser else json.loads(request.data)

    if request.cookies.get("userid"):
        userData = getUserData(request.cookies.get("userid"))   # Retrieves dictionary of userData from the util function

        if userData not in getGroupUsers(data["groupid"]) and not userData["admin"]:    # If the user isn't in the group
            if isBrowser:                                                               # and isn't an admin
                return redirect(url_for("dash", msg="You're not allowed to send emails to this group"))
            else:
                return json.dumps({
                    "code": 401,
                    "msg": "You don't have permission to send emails to this group"
                }), 401

        sendGroupEmail(data["groupid"], data, userData)         # User data, groupid, and email data sent to the send email util function
    else:
        if isBrowser:
            return redirect(url_for("index", code=403, msg="You must be signed in to do this!"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
            }), 403

    if isBrowser:
        return redirect(url_for('group', id=data["groupid"], msg="Email sent successfully"))
    else:
        return json.dumps({
            "code": 200,
            "msg": "Your message has been sent!"
        })