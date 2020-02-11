from src.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class FileGroupTable(db.Model):
    __tablename__ = "filegrouptable"

    fileid = db.Column(UUID(as_uuid=True), db.ForeignKey('filetable.fileid'), primary_key=True)
    groupid = db.Column(UUID(as_uuid=True), db.ForeignKey('grouptable.groupid'), primary_key=True)

    def __init__(self, data):
        self.groupid = data["groupid"]
        self.fileid = data["fileid"]
