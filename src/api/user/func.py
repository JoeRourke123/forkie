from app import db

from src.db.UserTable import UserTable


def getUserData(userid):
    return UserTable.query.filter_by(userid=userid).first()