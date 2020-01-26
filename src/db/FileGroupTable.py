from src.db import db


FileGroupTable = db.Table(
    'filegrouptable',
    db.Column('fileid', db.String(128), db.ForeignKey('filetable.fileid'), primary_key=True),
    db.Column('groupid', db.String(128), db.ForeignKey('grouptable.groupid'), primary_key=True)
)
