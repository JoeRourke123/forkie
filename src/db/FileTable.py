from src.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid


class FileTable(db.Model):
    __tablename__ = "filetable"
    fileid = db.Column(UUID(as_uuid=True), primary_key=True)
    filename = db.Column(db.String(64), nullable=False)

    def __init__(self, data):
        self.fileid = str(uuid.uuid1())
        self.filename = data["filename"]
