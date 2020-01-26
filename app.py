from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
	return "<h1>Hello!</h1>"

if __name__ == "main":
	app.run(threaded=True, port=5000)
