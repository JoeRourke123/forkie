from src.db.UserTable import UserTable
from src.db.GroupTable import GroupTable
from src.db.FileTable import FileTable
from src.db.FileGroupTable import FileGroupTable

from src.api.groups.utils import getUserGroups


def getUserData(userid):
    return UserTable.query.filter(UserTable.userid == userid).first()

def getFilesUserCanAccess(userid: str):
    """ Returns the Query of the files that the user (userid) can access. This is the join of
        FileTable, UserTable and FileGroupTable: where FileTable.fileid = FileGroupTable.fileid AND
        (if the user is not part of the admin group then) WHERE FileGroupTable.groupid in groupids. THIS
        ASSUMES THAT EVERY FILE HAS A GROUP RELATION IN FileGroupTable. Also assumes that no other group
        will have the name "admin".
        - userid: retrieves all the files that this user can access 
        - returns: the SQLAlchemy query object for the query of all accessible files
    """
    groups = getUserGroups(userid)
    groupids = [group.groupid for group in groups]
    groupnames = [group.groupname for group in groups]
    # print(groupids)
    query = FileTable.query.join(FileGroupTable).join(GroupTable)\
        .add_columns(FileTable.fileid, FileTable.filename, GroupTable.groupname, GroupTable.groupid)\
        .filter((FileGroupTable.fileid == FileTable.fileid) & (FileGroupTable.groupid == GroupTable.groupid))
    if "admin" not in groupnames:
        for groupid in groupids:
            query = query.filter(FileGroupTable.groupid == groupid)
    return query
