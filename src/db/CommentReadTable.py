from src.db import db
from sqlalchemy.dialects.postgresql import UUID

from src.db.CommentTable import CommentTable
from src.db.UserTable import UserTable


class CommentReadTable(db.Model):
    __tablename__ = "commentreadtable"

    userid = db.Column('userid', UUID(as_uuid=True), db.ForeignKey('usertable.userid', ondelete='CASCADE'), primary_key=True)
    commentid = db.Column('commentid', UUID(as_uuid=True), db.ForeignKey('commenttable.commentid', ondelete='CASCADE'), primary_key=True)

    user = db.relationship(UserTable, foreign_keys=userid, backref=db.backref('commenter', lazy='joined', cascade="all, delete-orphan"))
    comment = db.relationship(CommentTable, foreign_keys=commentid, backref=db.backref('commented', lazy='joined', cascade="all, delete-orphan"))


    def __init__(self, data):
        self.commentid = data["commentid"]
        self.userid = data["userid"]