from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import json
from flask_heroku import Heroku

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

heroku = Heroku(app)
db = SQLAlchemy(app)

@app.route("/")
def index():
    return "<h1>Hello!</h1>"


if __name__ == "main":
    app.run(threaded=True, port=5000)
