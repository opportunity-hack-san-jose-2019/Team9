from flask import Flask, render_template
import pymysql
import configparser

# setting up configurations and constants
config = configparser.ConfigParser()
config.read('config.ini')

application = Flask(__name__)

rds_host = config['RDS']['RDSHost']
rds_name = config['RDS']['RDSName']
rds_password = config['RDS']['RDSPassword']
db_name = config['RDS']['DBName']
instance_name = config['RDS']['InstanceName']

@application.route("/")
def hello():
	print
	conn = pymysql.connect(rds_host, user=rds_name, passwd=rds_password, db=db_name, connect_timeout=5)
	data = list()
	query = "SELECT * FROM {}.PERSON".format(instance_name)

	with conn.cursor() as cur:
		cur.execute(query)
		for item in cur:
			print (item)

	return "Hello World!"

@application.route('/home')
def home():
	# return render_template('home.html', data = data, title="CS 218 Image Portal - Home Feed")
	return render_template('admin.html', title="Braven Admin Page")

if __name__ == "__main__":
	application.run()
