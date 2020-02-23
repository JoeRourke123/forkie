from src.db import db
from src.db.FileVersionTable import FileVersionTable
from sqlalchemy.dialects.postgresql import UUID
import uuid


class MetadataTable(db.Model):
    __tablename__ = "metadatatable"

    metadataid = db.Column(UUID(as_uuid=True), primary_key=True)
    versionid = db.Column(UUID(as_uuid=True), db.ForeignKey('fileversiontable.versionid', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(128), nullable=False)

    version = db.relationship(FileVersionTable, foreign_keys=versionid, backref=db.backref('version', lazy='joined', cascade="all, delete-orphan"))


    def __init__(self, data):
        self.metadataid = str(uuid.uuid1())
        self.versionid = data["versionid"]
        self.title = data["title"]
        self.value = data["value"]
