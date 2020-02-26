from traceback import print_exc

from sqlalchemy import and_

import src.api.files.file_query
from src.api.user.utils import getUserData
from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db.UserTable import UserTable


def getUserGroups(userID):
    try:
        res = GroupTable.query.join(UserGroupTable).filter(UserGroupTable.userid == userID).all()
        return list(map(lambda x: x.serialise(), res))
    except Exception as e:
        return print_exc()


def isGroupLeader(userID, groupID):
    try:
        res = GroupTable.query.filter(and_(GroupTable.groupleaderid == userID, GroupTable.groupid == groupID))
        return res.count() > 0
    except Exception as e:
        print(print_exc())
        return False


def getGroupUsers(groupID):
    try:
        res = UserTable.query.join(UserGroupTable, and_(UserGroupTable.userid == UserTable.userid,
                                                        UserGroupTable.groupid == groupID)).all()
        return list(map(lambda user: getUserData(user.userid), res))
    except Exception as e:
        print(print_exc())
        return []


def getGroupData(groupID):
    groupData = GroupTable.query.filter_by(groupid=groupID).first()

    return {
        "groupid": groupID,
        "members": getGroupUsers(groupID),
        "files": src.api.files.file_query.file_query({"groupid": groupID}),
        "groupname": groupData.groupname,
        "groupleader": getUserData(groupData.groupleaderid),

    }
