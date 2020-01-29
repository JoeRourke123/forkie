from src.db import db
from src.db.UserTable import UserTable
from src.db.FileVersionTable import FileVersionTable

from sqlalchemy.dialects.postgresql import UUID
import uuid

class CommentTable(db.Model):
    __tablename__ = "commenttable"
    commentid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    versionid = db.Column(UUID(as_uuid=True), db.ForeignKey('fileversiontable.versionid'), nullable=False)
    userid = db.Column(UUID(as_uuid=True), db.ForeignKey('usertable.userid'), nullable=False)
    comment = db.Column(db.String(256), nullable=False)
    date = db.Column(db.DateTime())

    user = db.relationship(UserTable, foreign_keys=userid, backref=db.backref('user', lazy='joined'), lazy='joined')
    file = db.relationship(FileVersionTable, foreign_keys=versionid, backref=db.backref('file', lazy='joined'), lazy='joined')

    def __init__(self, data):
        self.versionid = data['versionid']
        self.userid = data['userid']
        self.comment = data['comment']
        self.date = data['date']
