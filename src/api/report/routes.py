import io

from flask import Blueprint, request, redirect, url_for, make_response, send_file

import json
import os

from traceback import print_exc
from sqlalchemy import and_

from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db.UserTable import UserTable

from src.db import db

from src.api.user.utils import getUserData, getUserDataFromEmail
from src.api.groups.utils import getUserGroups, getGroupDataFromName, getGroupUsers
from src.api.report.utils import generateReportHTML, linkCSSToReport, generatePdfFromHtml

reportBP = Blueprint('report', __name__,
                     template_folder='../../templates',
                     static_folder='../../static',
                     url_prefix='/api/report')


@reportBP.route("/generateReport", methods=["POST"])
@reportBP.route("/generateReport/<groupname>.pdf", methods=["POST"])
def generateReport(groupname=None):
    """ JSON requires either groupid or email of a user and userid inside cookie.
        - If only email is specified then a report is generated on user. Querying
        - If only groupid is specified then a report is generated on user (also now accepts groupname)
        - If both then a report is generated on the user's activity within said group
    """
    isBrowser = "email" in request.form or "groupid" in request.form
    data = request.form if isBrowser else json.loads(request.data)
    data = dict(data)
    cookie_userid = request.cookies.get('userid')

    if cookie_userid:
        try:
            # First check if user requesting report has the permission to do this. If the user is admin then
            # skip over this bit
            if 'groupname' in data:
                data['groupid'] = str(getGroupDataFromName(data['groupname']).groupid)
            user_groups = getUserGroups(cookie_userid)
            print("Generating a report for " + cookie_userid + " subject:", data)
            user_info = getUserData(cookie_userid)
            permission = True
            if not user_info['admin']:
                user_groupleader = next((group for group in user_groups if group['groupleaderid'] == cookie_userid), None)
                if 'groupid' in data:
                    if user_groupleader is None:
                        permission = False
                else:
                    data['groupid'] = None
                if 'email' in data:
                    if next((user for user in getGroupUsers(user_groupleader['groupid']) if getUserData(user['userid'])['email'] == data['email']), None) is None:
                        permission = False
                else:
                    data['email'] = None

            if not permission:
                if isBrowser:
                    return redirect(url_for('dash', msg="Sorry you are not permitted to complete this action"))
                else:
                    return json.dumps({
                        "code": 401,
                        "msg": "You don't have permission to complete this action!"
                    }), 401

            if isBrowser:
                return send_file(
                    generatePdfFromHtml(generateReportHTML(data.get("groupid"), data.get("email"))),
                    attachment_filename=groupname + ".pdf"
                )
            else:
                return json.dumps({
                    "code": 200,
                    "msg": "Report has been created!",
                    "report": generateReportHTML(data.get("groupid"), data.get("email"))
                })
        except Exception as e:
            print(print_exc())

            if isBrowser:
                return redirect(url_for("group", id=data["groupid"], msg="Something went wrong while generating your report"))
            else:
                return json.dumps({
                    "code": 500,
                    "msg": "Something went wrong when generating report."
                }), 500
    else:
        if isBrowser:
            return redirect(url_for("index", msg="You must be signed in to do this"))
        else:
            return json.dumps({
                "code": 403,
                "msg": "You must be signed in to do this",
            }), 403