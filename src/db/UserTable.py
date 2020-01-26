from src.db import db

class UserTable(db.Model):
    userid = db.Column(db.String(128), primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(355), unique=True, nullable=False)
    lastlogin = db.Column(db.DateTime, nullable=False)

    def __init__(self, data):
        self.userid = "" # Place in once utils key hash function implemented
        self.username = data["username"]
        self.password = data["password"]
        self.email = data["email"]
        self.lastlogin = data["lastlogin"]
