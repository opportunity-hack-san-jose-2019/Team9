from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import hashlib
import pymysql
import configparser
from dal import *
import re
from schedule import *
import csv

# setting up configurations and constants
config = configparser.ConfigParser()
config.read('config.ini')

application = Flask(__name__)

rds_host = config['RDS']['RDSHost']
rds_name = config['RDS']['RDSName']
rds_password = config['RDS']['RDSPassword']
db_name = config['RDS']['DBName']
instance_name = config['RDS']['InstanceName']

application.secret_key = "6t813eiyrgqhdjksancbgtqerdhiuoaslknc"

def getConnection():
  con = pymysql.connect(rds_host, user=rds_name, passwd=rds_password, db=db_name, connect_timeout=5)
  return con

def isAdmin():
	if session:
		try:
			if getPersonType(session['id']) == 0:
				return True
		except KeyError:
			return False
	return False

def isSession():
	if 'loggedin' in session:
		return True
	return False

@application.route('/', methods=['GET', 'POST'])
def login():
	# get connection object
	con = getConnection()

	# Output message if something goes wrong
	msg = ''

	# Check if "username" and "password" POST requests exist (user submitted form)
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		# Create variables for easy access
		username = request.form['username']
		password_object = hashlib.md5(request.form['password'].encode())
		password = password_object.hexdigest()
		print ("U/P: {}/{}".format(username, password))
		# Check if account exists using MySQL
		cur = con.cursor()
		query = 'SELECT P_ID, P_TYPE FROM {}.PERSON WHERE P_EMAIL = "{}" AND P_PASS = "{}"'.format(instance_name, username, password)
		cur.execute(query)
		# Fetch one record and return result
		account = cur.fetchone()
		# If account exists in accounts table in out database
		if account:
			print ("Here")
			# Create session data, we can access this data in other routes
			session['loggedin'] = True
			session['id'] = account[0]
			# Redirect to home page
			print ("Person Type: ", getPersonType(session['id']))
			if getPersonType(session['id']) == 0:
				return 'admin_page'
			elif getPersonType(session['id']) == 1:
				return redirect(url_for('profile'))
			elif getPersonType(session['id']) == 2:
				return redirect(url_for('profile'))
			else:
				return 'There was an error, please login error'
		else:
			# Account doesnt exist or username/password incorrect
			msg = 'Incorrect username/password!'
		cur.close()

	con.close()
	# Show the login form with message (if any)
	return render_template('index.html', msg=msg)

@application.route('/homes')
def homes():
	# return render_template('home.html', data = data, title="CS 218 Image Portal - Home Feed")
	return render_template('admin.html', title="Braven Admin Page")

@application.route('/logout')
def logout():
	# Remove session data, this will log the user out
	session.pop('loggedin', None)
	session.pop('id', None)
	# Redirect to login page
	return redirect(url_for('login'))

@application.route('/updatestudents', methods=['GET', 'POST'])
def updatestudents():
	if request.method == 'POST':
		print ("POST REQUEST")
		print (type(request.form))
		print (request.form)
		result = getQueryResult("SELECT S_ID FROM {}.STUDENT".format(instance_name))
		print ("RES", result)
		for item in result:
			print ("item", item)
			if 'selectedStudent_{}'.format(item[0]) in request.form:
				query = 'UPDATE {}.PERSON SET P_TYPE=10 WHERE P_ID = {}'.format(instance_name, item[0])
				print ("Unenrolled student", item[0])
				con = getConnection()
				cur=con.cursor()
				cur.execute(query)
				con.commit()
	return redirect(url_for('viewstudents'))


@application.route("/viewstudents", methods=['GET'])
def viewstudents():
	if isAdmin():
		try:
			# con = getConnection()
			# cursor = con.cursor()
			query = "SELECT * from team9.PERSON WHERE P_TYPE = 1"
			# result = cursor.execute("SELECT * from team9.STUDENT;")
			result = getQueryResult(query)
			print ("Result:", result)
			all_students = list()
			if result:
				for student in result:
					student_details_query = "SELECT P_FNAME, P_LNAME, P_EMAIL FROM team9.PERSON WHERE P_ID = {}".format(student[0])
					student_details = getQueryResult(student_details_query, fetchOne=True)
					print ("SD:", student_details)
					new_student = {
						'S_ID': student[0],
						'S_NAME': student_details[0] + " " + student_details[1],
						'S_EMAIL': student_details[2],
						'S_ATTENDANCE': student[1],
						'S_PROJECT': student[2],
						'S_GRADE': student[3],
						'S_CLASS': student[4]
					}
					all_students.append(new_student)
				print ("Returning JSON")
				return render_template('viewstudents.html', data=all_students)
			else:
				return jsonify('No data!'), 404
		except Exception as err:
			print(str(err))
			return (None, 500)
	else:
		print ("---------")
		return jsonify("",401)


@application.route('/home')
def home():
	# Check if user is loggedin
	if isSession():
		return render_template('home.html', username=getPersonName(session['id']))
	return redirect(url_for('login'))


@application.route('/profile')
def profile():
	# Check if user is loggedin
	if isSession():
		# We need all the account info for the user so we can display it on the profile page
		query = 'SELECT P_ID, P_EMAIL, P_PHONE FROM {}.PERSON WHERE P_ID = {}'.format(instance_name, session['id'])
		account = getQueryResult(query, fetchOne=True)
		print ("Account", account)
		# Show the profile page with account info
		return render_template('profile.html', account=account)
	# User is not loggedin redirect to login page
	return redirect(url_for(''))


@application.route('/register', methods=['GET', 'POST'])
def register():
	# Output message if something goes wrong...
	msg = ''
	# Check if "username", "password" and "email" POST requests exist (user submitted form)
	if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
		# Create variables for easy access
		fname = request.form['fname']
		lname = request.form['lname']
		password_object = hashlib.md5(request.form['password'].encode())
		password = password_object.hexdigest()
		email = request.form['email']
		type = int(request.form['type'])
		phone = request.form['phone']
		con = getConnection()
		cur = con.cursor()
		query = "SELECT * FROM {}.PERSON WHERE P_EMAIL = '{}'".format(instance_name, email)
		cur.execute(query)
		account = cur.fetchone()
		cur.close()
		print ("Here")
		print (fname, lname, type, email, phone, password)
		# If account exists show error and validation checks
		if account:
			msg = 'Account already exists!'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address!'
		elif not password or not email:
			msg = 'Please fill out the form!'
		else:
			# Account doesnt exists and the form data is valid, now insert new account into accounts table
			con = getConnection()
			cur=con.cursor()
			maxPersonId = getQueryResult('SELECT MAX(P_ID) from {}.PERSON'.format(instance_name), fetchOne=True)[0] + 1
			cur.execute("INSERT INTO {}.PERSON VALUES ({}, '{}', '{}', {}, '{}', '{}', '{}')".format(instance_name, maxPersonId, fname, lname, type, email, phone, password))
			con.commit()
			msg = 'You have successfully registered!'
			cur.close()
	elif request.method == 'POST':
		# Form is empty... (no POST data)
		msg = 'Please fill out the form!'
	# Show registration form with message (if any)
	return render_template('register.html', msg=msg)

@application.route('/newevent', methods=['GET', 'POST'])
def newevent():
	if request.method == 'POST':
		if len(request.form['eventId']) < 1:
			eID = getQueryResult('SELECT MAX(E_ID) from {}.EVENT'.format(instance_name), fetchOne=True)[0] + 1
		else:
			eID = request.form['eventId']

		name = request.form['eventName']
		date = request.form['eventDate']
		start_time = request.form['startTime']
		end_time = request.form['endTime']
		print (date)
		query = "INSERT INTO {}.EVENT VALUES ({}, '{}', STR_TO_DATE('{}', '%Y-%m-%d'), STR_TO_DATE('{}', '%H:%i'), STR_TO_DATE('{}', '%H:%i'))".format(instance_name, eID, name, date, start_time, end_time)
		con = getConnection()
		cur = con.cursor()
		cur.execute(query)
		con.commit()
		cur.close()

		print ("Sending emails")
		students = getQueryResult("SELECT P_EMAIL FROM {}.PERSON WHERE P_TYPE=1".format(instance_name))
		for student_email in students:
			print ("Sending email to ", student_email[0])
			mailTrigger(student_email[0], "SUBJECT: New Event Created \n \n\n Hello student, {} has been created for {}, starting at {} and ending at {}"
			.format(name, date, start_time, end_time))

		interviewers = getQueryResult("SELECT P_EMAIL FROM {}.PERSON WHERE P_TYPE=2".format(instance_name))
		for interviewer_email in interviewers:
			mailTrigger(interviewer_email[0], "SUBJECT: New Event Created \n \n\n Hello interviewer, {} has been created for {}, starting at {} and ending at {}"
				.format(name, date, start_time, end_time))


		# # uploading csv
		# if 'attachment_1' in request.files:
		# 	csvfile = request.files['attachment_1']
		# 	reader = csv.DictReader(csvfile)
		# 	data = [row for row in reader]
		# 	for row in data:
		# 		date_time_store = row['date_time']
		# 	technician_store = row['technician']
		# 	test_location_store = row['test_location']
		# 	product_serial_number_store = row['product_serial_number']
		# 	test_detail_store = row['test_detail']
		# 	test_result_store = row['test_result']




		return "Event Added"

	return render_template('newevent.html')


@application.route('/updateinterviewer', methods=['GET', 'POST'])
def updateinterviewer():
	print ("In update interviewer")
	if request.method == 'POST':
		print ("In post")
		result = getQueryResult("SELECT P_ID FROM {}.PERSON WHERE P_TYPE = 2".format(instance_name))
		for item in result:
			if 'selectedStudent_{}'.format(item[0]) in request.form:
				query = 'UPDATE {}.PERSON SET P_TYPE=10 WHERE P_ID = {}'.format(instance_name, item[0])
				print ("Unenrolled student", item[0])
				con = getConnection()
				cur=con.cursor()
				cur.execute(query)
				con.commit()
	return redirect(url_for('viewinterviewers'))

@application.route("/viewinterviewers", methods=['GET'])
def viewinterviewers():
	if isAdmin():
		try:
			# con = getConnection()
			# cursor = con.cursor()
			query = "SELECT * from team9.PERSON WHERE P_TYPE = 2"
			# result = cursor.execute("SELECT * from team9.STUDENT;")
			result = getQueryResult(query)
			print ("Result:", result)
			all_students = list()
			if result:
				for student in result:
					interviewer_details_query = "SELECT P_FNAME, P_LNAME, P_EMAIL FROM team9.PERSON WHERE P_ID = {}".format(student[0])
					interviewer_details = getQueryResult(interviewer_details_query, fetchOne=True)
					print ("SD:", interviewer_details)
					new_student = {
						'P_ID': student[0],
						'P_NAME': interviewer_details[0] + " " + interviewer_details[1],
						'P_EMAIL': interviewer_details[2],
					}
					all_students.append(new_student)
				print ("Returning JSON")
				return render_template('viewinterviewers.html', data=all_students)
			else:
				return jsonify('No data!'), 404
		except Exception as err:
			print(str(err))
			return (None, 500)
	else:
		print ("---------")
		return jsonify("",401)

# scheduling

@application.route('/generatematches', methods=['GET', 'POST'])
def getMatches():
	if request.method == 'POST' or request.method == 'GET':
		# eID = getSelectedEvent()
		eID = 1
		query = "SELECT E_START, E_END FROM {}.EVENT WHERE E_ID = {}".format(instance_name, eID)
		result = getQueryResult(query, fetchOne=True)
		start_time = str(result[0]).split(":")
		end_time = str(result[1]).split(":")
		start_time = start_time[0] + start_time[1]
		end_time = end_time[0] + end_time[1]
		matches, eventID = scheduleInterviewes(start_time, end_time, event_id=eID)

		for match in matches:
			settMatch(match[0], match[1], match[2], match[3], eventID)


	return "Matches done"





# @upload_csv_blueprint.route('/upload_csv', methods=['GET','POST'])
# def upload_file():
# 	if request.method == 'POST':
# 		csvfile = request.files['file']
# 		reader = csv.DictReader(csvfile)
# 		data = [row for row in reader]
# 		for row in data:
# 			date_time_store = row['date_time']
# 			technician_store = row['technician']
# 			test_location_store = row['test_location']
# 			product_serial_number_store = row['product_serial_number']
# 			test_detail_store = row['test_detail']
# 			test_result_store = row['test_result']
#
# 			query = test_result(date_time = date_time_store,
# 				technician_name = technician_store,
# 				place_of_test = test_location_store,
# 				serial_number=product_serial_number_store,
# 				test_details=test_detail_store,
# 				result=test_result_store)
#
# 			db.session.add(query)
# 			db.session.commit()
# 			return('Did it work?')
# 		else:
# 			return redirect(url_for('upload_csv.upload_csv_layout'))

if __name__ == "__main__":
	application.run()





# aseem

# @app.route("/student", methods=["POST", "PUT"])
# def add_recipe():
# 	req_data = request.get_json()
# 	S_ATTENDANCE = req_data['S_ATTENDANCE']
# 	S_PROJECT = req_data['S_PROJECT']
# 	S_GRADE = req_data['S_GRADE']
# 	S_CLASS = req_data['S_CLASS']
# 	try:
# 		conn = mysql.get_db()
# 		cursor = conn.cursor()
# 		if request.method == "POST":
# 			cursor.execute(
# 				"""INSERT INTO
#             team9.STUDENT (
#                 S_ATTENDANCE,
#                 S_PROJECT,
#                 S_GRADE,
#                 S_CLASS
#                 )
#         VALUES (%s, %s, %s, %s)""",
# 				(S_ATTENDANCE, S_PROJECT, S_GRADE, S_CLASS))
# 		elif request.method == "PUT":
# 			cursor.execute(
# 				"""UPDATE
#             students SET
#                 S_ATTENDANCE = %s,
#                 S_PROJECT = %s,
#                 S_GRADE = %s,
#                 S_CLASS= %s,
#                 WHERE S_ID = %s
#                     """, (S_ATTENDANCE, S_PROJECT, S_GRADE, S_CLASS))
# 		conn.commit()
# 		cursor.close()
# 		if request.method == "POST":
# 			return jsonify('Added the student'), 201
# 		elif request.method == "PUT":
# 			return jsonify('Updated the student'), 200
# 	except Exception as err:
# 		print(str(err))
# 		return jsonify('Add/Update recipe failed'), 500
# if __name__ == '__name__':
# 	app.run(debug=True)
