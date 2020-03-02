from datetime import datetime
from traceback import print_exc

from flask import request
from sqlalchemy import and_

from src.api.files.file_query import file_query
from src.api.groups.utils import getGroupUsers
from src.api.user.utils import getUserData
from src.db import db

from src.db.CommentReadTable import CommentReadTable
from src.db.CommentTable import CommentTable

""" Adds a comment to the database, given commentData and a userID
    - commentData: a form data dictionary, including at least fileID and comment fields
    - userid: a string representation of the UUID object associated with that user's database record
    - returns: void
"""
def addComment(commentData: dict, userid: str):
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
        print(print_exc())


""" Gets all the comments associated with a specified fileID
    - fileid: a string representation of the UUID object associated with the provided file's database record
    - returns: a list of comment records with the specified fileid field, mapped to dictionaries - or empty list if an error occurs
"""
def getComments(fileid: str, archived: bool = False):
    fileData = file_query({"fileid": fileid, "archived": archived})[0]
    groupMembers = []

    try:
        comments = CommentTable.query.filter(CommentTable.fileid == fileid).order_by(CommentTable.date.desc()).all()

        return list(map((lambda x: {
            "comment": x.comment,
            "date": x.date,
            "commentid": str(x.commentid),
            "file": fileid,
            "user": getUserData(str(x.userid)),     # User data of the commenter
            "read": False not in [commentRead(str(x.commentid), group["groupid"]) for group in fileData["groups"]]
        }), comments))      # Checks if all users from all groups have read the comment

    except Exception as e:
        print(print_exc())              # Prints any exceptions if they occur and returns an empty list
        return []


""" Retrieves all the unread comments from a specific user in a specific list of files
    - files: a list of file data, containing at least the fileid
    - userid: a string representation of the UUID object associated with that user's database record
    - returns: sorted, by date, list of comments from the provided files which the specified user has not read
"""
def getUnreadComments(files: list, userid: str):
    if not userid:  # If the user is not signed/doesn't have a cookie to provide the function
        return []

    unread = []

    for file in files:      # For each file, merge the list of unread comments into the 'unread' list
        unread.extend(      # Extend merges two lists together
            filter(lambda x: CommentReadTable.query.filter(and_(
                CommentReadTable.commentid == x["commentid"],
                CommentReadTable.userid == userid
            )).count() is not 1, getComments(file["fileid"]))   # Filters out the comments for which there exists a
        )                                                       # CommentRead entry from the user.

    return sorted(unread, key=lambda x: x["date"], reverse=True)  # Returns the list sorted by the comments' date field


""" Given a fileid, reads all the comments from that the provided user has not read
    - fileid: a string representation of the UUID object associated with that file's database record
    - userid: a string representation of the UUID object associated with that user's database record
    - returns: void
"""
def readUnreadComments(fileid: str, userid: str):
    if not userid:
        return

    try:
        unread = getUnreadComments([{"fileid": fileid}], userid)

        for comment in unread:
            readComment(comment["commentid"], userid)

        db.session.commit()
    except Exception as e:
        print(print_exc())

"""
    Tom's read comment implementation, adds level of abstraction from the readUnreadComments method
    - commentid: takes a string comment id to read
    - userid : takes a string user UUID to mark comment as read from
"""
def readComment(commentID, userID):
    entry = CommentReadTable({
        "commentid": commentID,
        "userid": userID
    })

    db.session.add(entry)
    db.session.commit()


def commentRead(commentID, groupID):
    """
    get all users in group
    for each user:
        if (userID, fileVersionID) is not in CommentReadTable:
            return False
    """

    # get all users in the group
    groupUsersQuery = getGroupUsers(groupID)

    # iterate through the users
    read_status = True
    for row in groupUsersQuery:
        userID = row["userid"]

        # check whether there is a log of the comment being read by this user
        commentReadQuery = CommentReadTable.query.filter(and_(CommentReadTable.userid == userID, CommentReadTable.commentid == commentID))

        # if the comment has not been read by this user
        # not all members of the group have read it, so the comment will be shown as being unread
        if not commentReadQuery:
            read_status = False

    return read_status