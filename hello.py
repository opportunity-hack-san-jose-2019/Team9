from flask import Flask
import pymysql

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello Worldsss!"

if __name__ == "__main__":
	app.run()
