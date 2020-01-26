from src.db import db, UserTable

class GroupTable(db.Model):
    groupid = db.Column(db.String(128), primary_key=True)
    groupname = db.Column(db.String(64), nullable=False)
    groupleaderID = db.Column('groupleader', db.String(128), db.ForeignKey('usertable.userid'), nullable=False)

    groupleader = db.relationship(UserTable, foreign_keys=groupleaderID, backref=db.backref('leader', lazy='joined'))

    def __init__(self, data):
        self.groupid = data["groupid"]
        self.groupname = data["groupname"]
        self.groupleaderID = data["groupleaderID"]
