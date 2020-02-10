from app import db

from src.db.UserTable import UserTable
from src.db.GroupTable import GroupTable
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
    # return db.session.query(UserGroupTable).filter(UserGroupTable.userid == userid).all()
    return GroupTable.query.join(UserGroupTable).join(UserTable)\
        .filter((UserGroupTable.c.userid == UserTable.userid) & (UserGroupTable.c.groupid == GroupTable.groupid)).all()

def getFilesUserCanAccess(userid: str):
    """ Returns the Query of the files that the user (userid) can access. This is the join of
        FileTable, UserTable and FileGroupTable: where FileTable.fileid = FileGroupTable.fileid AND
        FileGroupTable.groupid in groupids AND
    """
    groups = getUserGroupsID(userid)
    groupids = [group.groupid for group in groups]
    print(groupids)
    query = FileTable.query.join(FileGroupTable)\
        .add_columns(FileTable.fileid, FileTable.filename, GroupTable.groupid)\
        .filter(FileGroupTable.c.fileid == FileTable.fileid)
    if "admin" not in groupids:
        for groupid in groupids:
            query = query.filter(FileGroupTable.c.groupid == groupid)
    return query
