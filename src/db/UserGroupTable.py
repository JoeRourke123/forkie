from src.db import db


UserGroupTable = db.Table(
    'usergrouptable',
    db.Column('userid', db.String(128), db.ForeignKey('usertable.userid'), primary_key=True),
    db.Column('groupid', db.String(128), db.ForeignKey('grouptable.groupid'), primary_key=True)
)