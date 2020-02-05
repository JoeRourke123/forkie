from flask import current_app as app
from flask import render_template, Blueprint, request, redirect, url_for

errorsBP = Blueprint('groups', __name__,
                    template_folder='../../templates',
                    static_folder='../../static',
                    url_prefix='/error')

@errorsBP.route("/<code>")
def error(code=500, msg=None):
    return render_template("errors.html", code=code, msg=msg)
