from src.db import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
import uuid

class UserTable(db.Model):
    __tablename__ = "usertable"
    userid = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(355), unique=True, nullable=False)
    lastlogin = db.Column(db.DateTime)

    def __init__(self, data):
        self.username = data["username"]
        self.password = data["password"]
        self.email = data["email"]
        self.lastlogin = data["lastlogin"]
