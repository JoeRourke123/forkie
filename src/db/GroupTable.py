from src.db import db
from src.db.UserTable import UserTable
from sqlalchemy.dialects.postgresql import UUID
import uuid


class GroupTable(db.Model):
    __tablename__ = "grouptable"

    groupid = db.Column(UUID(as_uuid=True), primary_key=True)
    groupname = db.Column(db.String(64), nullable=False)
    groupleaderid = db.Column('groupleader', UUID(as_uuid=True), db.ForeignKey('usertable.userid'), nullable=False)

    groupleader = db.relationship(UserTable, foreign_keys=groupleaderid, backref=db.backref('leader', lazy='joined'))

    def __init__(self, data):
        self.groupid = str(uuid.uuid1())
        self.groupname = data["groupname"]
        self.groupleaderid = data["groupleaderid"]
