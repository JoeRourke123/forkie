from src.db import db
from sqlalchemy.dialects.postgresql import UUID

#test push

UserGroupTable = db.Table(
    'usergrouptable',
    db.Column('userid', UUID(as_uuid=True), db.ForeignKey('usertable.userid'), primary_key=True),
    db.Column('groupid', UUID(as_uuid=True), db.ForeignKey('grouptable.groupid'), primary_key=True)
)
