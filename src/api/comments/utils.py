from datetime import datetime

from src.api.user.utils import getUserData
from src.db import db

from src.db.CommentReadTable import CommentReadTable
from src.db.CommentTable import CommentTable

def addComment(commentData, fileid, userid):
    try:
        comment = CommentTable({
            "fileid": fileid,
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