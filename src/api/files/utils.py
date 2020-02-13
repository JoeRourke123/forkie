""" General utils for files API
"""
import os

def getFileExtension(filename: str) -> str:
    return os.path.splitext(filename)[1]