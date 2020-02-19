from flask import Blueprint

filesBP = Blueprint('files', __name__, template_folder='../../templates', static_folder='../../static', url_prefix='/api/files')
