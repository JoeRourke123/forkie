from src.db import db
from sqlalchemy.dialects.postgresql import UUID


FileGroupTable = db.Table(
    'filegrouptable',
    db.Column('fileid', UUID(as_uuid=True), db.ForeignKey('filetable.fileid'), primary_key=True),
    db.Column('groupid', UUID(as_uuid=True), db.ForeignKey('grouptable.groupid'), primary_key=True)
)
