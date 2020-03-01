from src.db.UserTable import UserTable
from src.db.GroupTable import GroupTable
from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable
from src.db.UserGroupTable import UserGroupTable

from sqlalchemy import and_

def getUserDataFromEmail(email: str):
    query = UserTable.query.filter(UserTable.email == email).first()
    
    return {
        "userid": query.userid,
        "username": query.username,
        "email": query.email,
        "lastlogin": query.lastlogin,
        "admin": query.admin
    }

def getUserData(userid):
    query = UserTable.query.filter(UserTable.userid == userid).first()

    return {
        "userid": query.userid,
        "username": query.username,
        "email": query.email,
        "lastlogin": query.lastlogin,
        "admin": query.admin
    }


def getFilesUserCanAccess(userid: str):
    """ Returns the Query of the files that the user (userid) can access. This is the join of
        FileTable, UserTable and FileGroupTable: where FileTable.fileid = FileGroupTable.fileid AND
        (if the user is not part of the admin group then) WHERE FileGroupTable.groupid in groupids. THIS
        ASSUMES THAT EVERY FILE HAS A GROUP RELATION IN FileGroupTable.
        - userid: retrieves all the files that this user can access 
        - returns: the SQLAlchemy query object for the query of all accessible files
    """

    userData = getUserData(userid)

    query = FileTable.query.join(FileGroupTable).join(GroupTable).join(UserGroupTable)\
        .filter(and_(FileGroupTable.fileid == FileTable.fileid, FileGroupTable.groupid == GroupTable.groupid, FileGroupTable.groupid == UserGroupTable.groupid, UserGroupTable.userid == userid))\

    if userData["admin"]:
        query = FileTable.query

    return query
