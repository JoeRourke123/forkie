from src.db import db
from sqlalchemy.dialects.postgresql import UUID

class CommentReadTable(db.Model):
    __tablename__ = "commentreadtable"

    userid = db.Column('userid', UUID(as_uuid=True), db.ForeignKey('usertable.userid'), primary_key=True)
    commentid = db.Column('commentid', UUID(as_uuid=True), db.ForeignKey('commenttable.commentid'), primary_key=True)

    def __init__(self, data):
        self.commentid = data["commentid"]
        self.userid = data["userid"]