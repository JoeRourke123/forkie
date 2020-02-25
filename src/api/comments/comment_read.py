from src.db.CommentReadTable import CommentReadTable
from src.db.FileVersionTable import FileVersionTable

from groups.utils import getGroupUsers

from traceback import print_exc

def commentRead(fileVersionID, groupID):
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
        userID = row[1]

        # check whether there is a log of the comment being read by this user
        commentReadQuery = CommentReadTable.query.join(CommentReadTable, and_(CommentReadTable.userid == userid, FileVersionTable.versionid == CommentReadTable.versionid))

        # if the comment has not been read by this user
        # not all members of the group have read it, so the comment will be shown as being unread
        if not commentReadQuery:
            read_status = False

    return read_status
