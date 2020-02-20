from src.db import db
from src.db.UserTable import UserTable
from src.db.FileTable import FileTable

from sqlalchemy.dialects.postgresql import UUID
import uuid

class CommentTable(db.Model):
    __tablename__ = "commenttable"
    commentid = db.Column(UUID(as_uuid=True), primary_key=True)
    fileid = db.Column(UUID(as_uuid=True), db.ForeignKey('filetable.fileid'), nullable=False)
    userid = db.Column(UUID(as_uuid=True), db.ForeignKey('usertable.userid'), nullable=False)
    comment = db.Column(db.String(256), nullable=False)
    date = db.Column(db.DateTime())

    user = db.relationship(UserTable, foreign_keys=userid, backref=db.backref('user', lazy='joined'), lazy='joined')
    file = db.relationship(FileTable, foreign_keys=fileid, backref=db.backref('file', lazy='joined'), lazy='joined')

    def __init__(self, data):
        self.commentid = str(uuid.uuid1())
        self.fileid = data['fileid']
        self.userid = data['userid']
        self.comment = data['comment']
        self.date = data['date']
