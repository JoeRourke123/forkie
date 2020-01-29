from src.db import db
from sqlalchemy.dialects.postgresql import UUID

CommentReadTable = db.Table(
    'commentreadtable',
    db.Column('userid', UUID(as_uuid=True), db.ForeignKey('usertable.userid'), primary_key=True),
    db.Column('commentid', UUID(as_uuid=True), db.ForeignKey('commenttable.commentid'), primary_key=True)
)