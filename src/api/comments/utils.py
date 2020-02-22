from datetime import datetime
from traceback import print_exc

from src.api.files.file_query import file_query
from src.api.groups.utils import getGroupUsers
from src.api.user.utils import getUserData
from src.db import db

from src.db.CommentReadTable import CommentReadTable
from src.db.CommentTable import CommentTable

def addComment(commentData, userid):
    try:
        comment = CommentTable({
            "fileid": commentData["fileid"],
            "userid": userid,
            "comment": commentData["comment"],
            "date": datetime.now()
        })

        db.session.add(comment)
        db.session.commit()

        commentRead = CommentReadTable({
            "commentid": comment.commentid,
            "userid": userid
        })

        db.session.add(commentRead)
        db.session.commit()
    except Exception as e:
        return str(e)


def getComments(fileid):
    comments = []
    fileData = file_query({"fileid": fileid})[0]
    groupMembers = []

    for group in fileData["groups"]:
        for member in getGroupUsers(group["groupid"]):
            if str(member["userid"]) not in groupMembers:
                groupMembers.append(str(member["userid"]))

    try:
        comments = CommentTable.query.filter(CommentTable.fileid == fileid).all()

        return list(map((lambda x: {
            "comment": x.comment,
            "date": x.date,
            "user": getUserData(str(x.userid)),
            "read": CommentReadTable.query.filter(CommentReadTable.commentid == str(x.commentid)).count() == len(groupMembers)
        }), comments))

    except Exception as e:
        print(print_exc())
        return comments


def getRecentComments():
    userFiles = file_query({})
    commentsList = []

    for file in userFiles:
        commentsList.extend(getComments(file["fileid"]))

    return sorted(commentsList, key=lambda x: x["date"], reverse=True)
