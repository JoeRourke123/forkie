from src.api.user.utils import getUserData
from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db.UserTable import UserTable

from sqlalchemy import and_

from traceback import print_exc

def getUserGroups(userID):
    try:
        return GroupTable.query.join(UserGroupTable).filter(UserGroupTable.userid == userID).all()
    except Exception as e:
        return print_exc()


def isGroupLeader(userID, groupID):
    try:
        res = GroupTable.query.filter(and_(GroupTable.groupleaderid==userID, GroupTable.groupid==groupID))
        return res.count() > 0
    except Exception as e:
        print(print_exc())
        return False


def getGroupUsers(groupID):
    try:
        res = UserTable.query.join(UserGroupTable, and_(UserGroupTable.userid == UserTable.userid, UserGroupTable.groupid == groupID)).all()
        return list(map(lambda user: getUserData(user.userid), res))
    except Exception as e:
        print(print_exc())
        return []


def getGroupData(groupID):
    return GroupTable.query.filter_by(groupid=groupID).first()
