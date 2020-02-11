from flask import Blueprint, request, redirect, url_for

import json
from traceback import print_exc
import os

from src.api.user.utils import getUserData
from src.api.groups.utils import getGroupUsers

import sendgrid

emailBP = Blueprint('email', __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/api/email')


@emailBP.route("/group", methods=["POST"])
def emailGroup():
    isBrowser = "groupID" in request.form
    data = request.form if isBrowser else request.data

    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

    if request.cookies.get("userid"):
        userData = getUserData(request.cookies.get("userid"))
        groupUsers = getGroupUsers(data["groupID"])

        if userData not in groupUsers:
            return redirect(url_for('errors.error', code=403, msg="You're not in this group so cannot send this message"))

        try:
            for user in groupUsers:
                mail = sendgrid.Mail("forkie@example.com", str(data["subject"] + " - from " + userData.email),
                                     str(user.email), str(data["content"]))
                response = sg.send(mail)
        except Exception as e:
            print(print_exc())
            return redirect(url_for('errors.error', code=500, msg=print_exc()))
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
        return redirect(url_for('emailSuccess', id=data["groupID"]))
    else:
        return json.dumps({
            "code": 200,
            "msg": "Your message has been sent!"
        })