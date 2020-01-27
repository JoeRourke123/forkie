from src.db import db, FileTable


class FileVersionTable(db.Model):
    versionid = db.Column(db.String(128), primary_key=True)
    fileid = db.Column(db.String(128), db.ForeignKey('filetable.fileid'), nullable=False)
    extension = db.Column(db.String(16), nullable=False)
    versionhash = db.Column(db.String(8), nullable=False)

    file = db.relationship(FileTable, foreign_keys=fileid, backref=db.backref('file', lazy='joined'))

    def __init__(self, data):
        self.versionid = "" # hash the time and user attempting to upload the version
        self.fileid = data["fileid"]
        self.extension = data["extension"]
        self.versionhash = data["versionhash"]
