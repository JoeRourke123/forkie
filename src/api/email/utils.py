import sendgrid
from sendgrid.helpers.mail import *
import os
from traceback import print_exc

import src.api.groups.utils  # import getGroupUsers, getGroupData
from src.api.user.utils import getAdmins

SG_KEY = os.environ.get('SENDGRID_API_KEY')

""" Util function which upon calling, with the correct parameters, sends an email to all members of a group.
    - groupid: the UUID of the group whose users will receive the email
    - data: the email data (must include the subject, and content of the email)
    - sender: the user data dictionary of the email sender/file uploader
    - returns: void
"""
def sendGroupEmail(groupid, data, sender):
    groupUsers = src.api.groups.utils.getGroupUsers(groupid)
    sg = sendgrid.SendGridAPIClient(SG_KEY)

    try:
        for user in groupUsers:
            mail = Mail(from_email="forkie@file-rep0.herokuapp.com",
                        subject=data["subject"] + " - from " + sender["username"],
                        to_emails=user["email"],
                        plain_text_content=data["content"])

            response = sg.send(mail)

    except Exception as e:
        print(print_exc())
        sendErrorEmail(groupid, data, sender)

""" Error handling function that is triggered upon error sending group email, sends 
    - groupid: the UUID of the group in which the bulk email was attempted
    - data: the attempted email data (must include the subject, and content of the email)
    - sender: the user data dictionary of the attempted email sender/file uploader
    - returns: void
"""
def sendErrorEmail(groupid, data, sender):
    admins = getAdmins()
    sg = sendgrid.SendGridAPIClient(SG_KEY)

    groupData = src.api.groups.utils.getGroupData(groupid)

    try:
        for admin in admins:
            mail = Mail(from_email="forkie-error@file-rep0.herokuapp.com",
                        subject="Error sending email to group " + groupData["groupname"],
                        to_emails=str(admin["email"]),
                        plain_text_content="""
                                    There was an error when %s uploaded a file and attempted to send an email to group %s (%s).
                                    
                                    Please attend to logs as soon as possible to resolve the issue.
                                    
                                    Here was the email content...
                                    "%s"
                                    
                                    Thank you,
                                    forkie Admin Alert
                                 """.format([sender["username"], groupData["groupid"], groupData["groupname"], data["content"]]))

            response = sg.send(mail)
    except Exception as e:
        print(print_exc())
