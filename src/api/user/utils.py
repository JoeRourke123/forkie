from app import db

from src.db.UserTable import UserTable
from src.db.UserGroupTable import UserGroupTable
from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable


def getUserData(userid):
    return UserTable.query.filter(UserTable.userid == userid).first()

def getUserGroupsID(userid: str) -> list:
    """ Returns the groupids of the groups that the user (of userid) is a member of
        - userid: the user to retrieve group info about
        - returns: list of groups containing member
    """
    print("Reached getUserGroupsID")
    return db.session.query(UserGroupTable).query.filter(UserGroupTable.userid == userid).all()

def getFilesUserCanAccess(userid: str):
    groups = getUserGroupsID(userid)
    print([group.groupid for group in groups])
    return FileTable.query.join(FileGroupTable, FileTable.fileid == FileGroupTable.fileid)\
        .add_columns(FileTable.fileid, FileTable.filename, FileGroupTable.groupid)\
        .filter(FileTable.fileid == FileGroupTable.fileid)\
        .filter(FileGroupTable.groupid in groupids if "admin" not in groupids else True)