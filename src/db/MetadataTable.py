from src.db import db, FileVersionTable
from sqlalchemy.dialects.postgresql import UUID
import uuid


class MetadataTable(db.Model):
    __tablename__ = "metadatatable"

    metadataid = db.Column(UUID(as_uuid=True), primary_key=True)
    versionid = db.Column(UUID(as_uuid=True), db.ForeignKey('fileversiontable.versionid'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(128), nullable=False)

    version = db.relationship(FileVersionTable, foreign_keys=versionid, backref=db.backref('file', lazy='joined'), lazy='joined')


    def __init__(self, data):
        self.metadataid = str(uuid.uuid1())
        self.versionid = data["versionid"]
        self.title = data["title"]
        self.value = data["value"]
