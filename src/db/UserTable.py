from src.db import db

class UserTable(db.Model):
    userid = db.Column(db.String(128), primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(355), unique=True, nullable=False)
    lastlogin = db.Column(db.DateTime, nullable=False)

    def __init__(self, data):
        self.userid = "@7bj?U!z5+QHD@Y8n2g@uwTbYMMD3?!^G#pCY*?t!F5mMzxvH?BG3dg%hejVAx=58X6xMt6PdCbc+7@Sg34?^zM-eX*Gz+Tgh9n_NaVL%=eV2s?Qfy3u&yVWvkw&=KB&" # Place in once utils key hash function implemented
        self.username = data["username"]
        self.password = data["password"]
        self.email = data["email"]
        self.lastlogin = data["lastlogin"]
