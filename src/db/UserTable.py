from src.db import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserTable(db.Model):
    __tablename__ = "usertable"

    userid = db.Column(UUID(as_uuid=True), primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(355), unique=True, nullable=False)
    admin = db.Column(db.Boolean(), unique=False, nullable=False, default=False)
    lastlogin = db.Column(db.DateTime)

    def __init__(self, data):
        self.userid = str(uuid.uuid1())
        self.username = data["username"]
        self.password = data["password"]
        self.email = data["email"]
        self.lastlogin = data["lastlogin"]
        self.admin = False

    def serialise(self):
        return {
            "userid": str(self.userid),
            "username": self.username,
            "email": self.email,
            "lastlogin": str(self.lastlogin),
            "admin": False
        }
