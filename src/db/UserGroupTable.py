from src.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid


class UserGroupTable(db.Model):
    __tablename__ = "usergrouptable"

    userid = db.Column(UUID(as_uuid=True), db.ForeignKey('usertable.userid'), primary_key=True)
    groupid = db.Column(UUID(as_uuid=True), db.ForeignKey('grouptable.groupid'), primary_key=True)

    def __init__(self, data):
        self.groupid = data["groupid"]
        self.userid = data["userid"]

