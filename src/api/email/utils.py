import sendgrid
import os
from traceback import print_exc

from src.api.groups.utils import getUserGroups

def sendGroupEmail(groupID, data, sender):
    groupUsers = getUserGroups(groupID)
    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

    try:
        for user in groupUsers:
            mail = sendgrid.Mail("forkie@example.com",
                                 str(user.email), str(data["subject"] + " - from " + sender.username),
                                 str(data["content"]))
            response = sg.send(mail)
            print(response.status_code)
            print(response.body)
            print(response.headers)
    except Exception as e:
        print(print_exc())
        # sendErrorEmail(groupID, data, sender)