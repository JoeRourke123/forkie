from src.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid


class FileTable(db.Model):
    __tablename__ = "filetable"
    fileid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    filename = db.Column(db.String(64), nullable=False)

    def __init__(self, data):
        fileid = "" # for when key generation method created - will be made from first file version time and filename
        filename = data["filename"]
