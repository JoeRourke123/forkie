from src.db import db
from src.db.FileTable import FileTable
from sqlalchemy.dialects.postgresql import UUID
import uuid


class FileVersionTable(db.Model):
    __tablename__ = "fileversiontable"

    versionid = db.Column(UUID(as_uuid=True), primary_key=True)
    fileid = db.Column(UUID(as_uuid=True), db.ForeignKey('filetable.fileid'), nullable=False)
    extension = db.Column(db.String(16), nullable=False)
    versionhash = db.Column(db.String(8), nullable=False)

    file = db.relationship(FileTable, foreign_keys=fileid, backref=db.backref('file', lazy='joined'))

    def __init__(self, data):
        self.versionid = str(uuid.uuid1())
        self.fileid = data["fileid"]
        self.extension = data["extension"]
        self.versionhash = data["versionhash"]
