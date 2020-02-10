from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db.UserTable import UserTable

from sqlalchemy import and_

from traceback import print_exc

def getUserGroups(userID):
    try:
        res = GroupTable.query.join(UserGroupTable, UserGroupTable.c.userid == userID).all()
        return res
    except Exception as e:
        return print_exc()


def isGroupLeader(userID, groupID):
    try:
        res = GroupTable.query.filter(and_(groupleader=userID, groupid=groupID)).first()
        return len(res) > 0
    except:
        print(print_exc())
        return False


def getGroupUsers(groupID):
    try:
        res = UserTable.query.join(UserGroupTable, and_(UserGroupTable.c.userid == UserTable.userid, UserGroupTable.c.groupid == groupID)).all()
        return res
    except Exception as e:
        print(print_exc())
        return []
