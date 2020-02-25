from src.db.CommentReadTable import CommentReadTable
from src.db.FileVersionTable import FileVersionTable

from groups.utils import getGroupUsers

from traceback import print_exc

def commentRead(fileVersionID, groupID):
    try:
        """
        get all users in group
        for each user:
            if (userID, fileVersionID) is not in CommentReadTable:
                return False
        """
        groupUsersQuery = getGroupUsers(groupID)

        read_status = True
        for row in groupUsersQuery:
            userID = row[1]

            commentReadQuery = CommentReadTable.query.join(CommentReadTable, and_(CommentReadTable.userid == userid, FileVersionTable.versionid == CommentReadTable.versionid))

            # if the comment has not been read by this user
            if not commentReadQuery:
                read_status = False

        return read_status
        
