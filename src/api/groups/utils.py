from traceback import print_exc

from sqlalchemy import and_

from src.api.user.utils import getUserData
from src.db.GroupTable import GroupTable
from src.db.UserGroupTable import UserGroupTable
from src.db.UserTable import UserTable


# Given a user ID will returns a list of serialised GroupTable rows
def getUserGroups(userID):
    try:
        res = GroupTable.query.join(UserGroupTable).filter(UserGroupTable.userid == userID).all()
        return list(map(lambda x: x.serialise(), res))  # Uses map with a lambda in order to convert
    except Exception as e:
        print(print_exc())
        return []       # If an


def getGroupUsers(groupID):
    """ Gets the user data of all the members of a group

        - groupid: the UUID of the group to get members of

        - returns: a response for the client to interpret based on the success of the operation
    """

    try:
        res = UserTable.query.join(UserGroupTable, and_(UserGroupTable.userid == UserTable.userid,
                                                        UserGroupTable.groupid == groupID)).all()   # Query to fetch all
        return list(map(lambda user: getUserData(user.userid), res))                                # members from group
    except Exception as e:
        print(print_exc())
        return []           # Returns an empty list if there is an exception



def getGroupData(groupID):
    from src.api.files import file_query

    """ Util function to get serialised group data, along with files accessible to the group

        - groupid: returns the serialised JSON data from a group, alongside all the files they can access

        - returns: a response for the client to interpret based on the success of the operation
    """

    groupData = GroupTable.query.filter_by(groupid=groupID).first()

    return {
        "groupid": groupID,
        "members": getGroupUsers(groupID),
        "files": file_query.file_query({"groupid": groupID}),  # Has to do absolute path of the module here
        "groupname": groupData.groupname,                                    # due to circular import error
        "groupleader": getUserData(groupData.groupleaderid),

    }


def getGroupDataFromName(groupname: str):
    """ Similar to get getGroupData but instead is passed the groupname. Will return the FIRST group with that name
    
        - groupname: the groupname to search for
        
        - returns: first grouptable object matching the groupname
    """
    return GroupTable.query.filter_by(groupname=groupname).first()
