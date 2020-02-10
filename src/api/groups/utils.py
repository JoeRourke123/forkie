from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db import db
from traceback import print_exc

def getUserGroups(userID):
    try:
        res = GroupTable.query.join(UserGroupTable, UserGroupTable.c.userid == userID).all()
        return res
    except Exception as e:
        return print_exc()
