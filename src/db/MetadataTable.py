from src.db import db, FileVersionTable


class MetadataTable(db.Model):
    metadataid = db.Column(db.String(128), primary_key=True)
    versionid = db.Column(db.String(128), db.ForeignKey('fileversiontable.versionid'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(128), nullable=False)

    version = db.relationship(FileVersionTable, foreign_keys=versionid, backref=db.backref('file', lazy='joined'), lazy='joined')


    def __init__(self, data):
        self.metadataid = ""
        self.versionid = data["versionid"]
        self.title = data["title"]
        self.value = data["value"]
