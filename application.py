from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import hashlib
import pymysql
import configparser
from dal import *
import re
from schedule import scheduleInterviewes
import csv
import io

# setting up configurations and constants
config = configparser.ConfigParser()
config.read('config.ini')

application = Flask(__name__)
print ("here")
UPLOAD_FOLDER = ''
ALLOWED_EXTENSIONS = {'txt', 'csv', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
				return redirect(url_for('/pythonlogin/home_admin'))
			elif getPersonType(session['id']) == 1:
				return redirect(url_for('home_student'))
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

@application.route('/home_student')
def home_student():
	# Check if user is loggedin
	print ("Home Student")
	if isSession():
		print ("In Session")
		# User is loggedin show them the home page
		return render_template('home_student.html', username=getPersonName(session["id"]))
	# User is not loggedin redirect to login page
	return redirect(url_for('login'))

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
			query = "SELECT * from team9.STUDENT"
			# result = cursor.execute("SELECT * from team9.STUDENT;")
			result = getQueryResult(query, fetchTop=15)
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
		if isAdmin():
			account = list()
			account.append(session["id"])
			account.append(getPersonName(session["id"]))
			account = tuple(account)
			return render_template('profile_admin.html', account=account)
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

		# print ("Sending emails")
		# students = getQueryResult("SELECT P_EMAIL FROM {}.PERSON WHERE P_TYPE=1".format(instance_name))
		# for student_email in students:
		# 	print ("Sending email to ", student_email[0])
		# 	mailTrigger(student_email[0], "SUBJECT: New Event Created \n \n\n Hello student, {} has been created for {}, starting at {} and ending at {}"
		# 	.format(name, date, start_time, end_time))
		#
		# interviewers = getQueryResult("SELECT P_EMAIL FROM {}.PERSON WHERE P_TYPE=2".format(instance_name))
		# for interviewer_email in interviewers:
		# 	mailTrigger(interviewer_email[0], "SUBJECT: New Event Created \n \n\n Hello interviewer, {} has been created for {}, starting at {} and ending at {}"
		# 		.format(name, date, start_time, end_time))


		# uploading csv
		# if 'attachment_1' in request.files:
		# 	print ("attachment provided")
		# 	csvfile = request.files['attachment_1']
		# 	reader = csv.DictReader(csvfile)
		# 	data = [row for row in reader]
		#   for row in data:

		f = request.files['attachment_1']
		if not f:
			pass
		else:
			print ("File passed")
			stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
			csv_input = csv.reader(stream)
			print(csv_input)
			next(csv_input)
			for row in csv_input:
				s_id = row[0]
				fname = row[1]
				lname = row[2]
				class_schedule = row[3]
				phone = row[4]
				email = row[5]
				career_interests = row[6]
				attendance = row[7]
				project = row[9]
				grade = row[8]
				con = getConnection()
				cur = con.cursor()
				query = "SELECT * FROM {}.PERSON WHERE P_ID = '{}'".format(instance_name, s_id)
				cur.execute(query)
				account = cur.fetchone()
				cur.close()
				# If account exists show error and validation checks
				if account:
					con = getConnection()
					cur=con.cursor()
					cur.execute("UPDATE {}.PERSON SET P_FNAME = '{}', P_LNAME = '{}', P_EMAIL = '{}', P_PHONE= '{}' WHERE P_ID = {}".format(instance_name, fname, lname, lname, email, phone, s_id))
					con.commit()
					cur.close()
					cur=con.cursor()
					cur.execute("UPDATE {}.STUDENT SET S_ATTENDANCE={}, S_PROJECT={}, S_GRADE={}, S_CLASS='{}' WHERE S_ID = {}".format(instance_name, attendance, project, grade, class_schedule, s_id))
					con.commit()
					cur.close()
				else:
					dummy_password = 'e2fc714c4727ee9395f324cd2e7f331f'
					con = getConnection()
					cur=con.cursor()
					cur.execute("INSERT INTO {}.PERSON VALUES ({}, '{}', '{}', 1, '{}', '{}', '{}')".format(instance_name, s_id, fname, lname, email, phone, dummy_password))
					con.commit()
					cur.close()
					cur=con.cursor()
					cur.execute("INSERT INTO {}.STUDENT VALUES ({}, {}, {}, {}, '{}')".format(instance_name, s_id, attendance, project, grade, class_schedule))
					con.commit()
					cur.close()
				interests = career_interests.strip().split(";")
				con = getConnection()
				cur=con.cursor()
				cur.execute("DELETE FROM {}.INT_MAPPING WHERE P_ID = {}".format(instance_name, s_id))
				con.commit()
				cur.close()
				for interest in interests:
					interest = getInterestNumber(interest)
					con = getConnection()
					cur=con.cursor()
					cur.execute("INSERT INTO {}.INT_MAPPING VALUES ({}, {})".format(instance_name, s_id, interest))
					con.commit()
					cur.close()

		f = request.files['attachment_2']
		if not f:
			pass
		else:
			print ("Mentor file passed")
			stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
			csv_input = csv.reader(stream)
			print(csv_input)
			next(csv_input)
			for row in csv_input:
				i_id = row[0]
				fname = row[1]
				lname = row[2]
				email = row[3]
				phone = row[4]
				vip = row[5]
				role = row[6]
				career_interests = row[7]
				attendance = row[7]
				class_schedule = row[8]
				con = getConnection()
				cur = con.cursor()
				query = "SELECT * FROM {}.PERSON WHERE P_ID = '{}'".format(instance_name, i_id)
				cur.execute(query)
				account = cur.fetchone()
				cur.close()
				# If account exists show error and validation checks
				if account:
					print ("In if account")
					con = getConnection()
					cur=con.cursor()
					cur.execute("UPDATE {}.PERSON SET P_FNAME = '{}', P_LNAME = '{}', P_EMAIL = '{}', P_PHONE= '{}' WHERE P_ID = {}".format(instance_name, fname, lname, email, phone, i_id))
					con.commit()
					cur.close()
					cur=con.cursor()
					cur.execute("UPDATE {}.INTERVIEWER SET VIP={}, CLASS='{}', ROLE='{}' WHERE I_ID = {}".format(instance_name, getVIPStatus(vip), class_schedule, role, i_id))
					con.commit()
					cur.close()
				else:
					print ("In else")
					dummy_password = 'e2fc714c4727ee9395f324cd2e7f331f'
					con = getConnection()
					cur=con.cursor()
					cur.execute("INSERT INTO {}.PERSON VALUES ({}, '{}', '{}', 2, '{}', '{}', '{}')".format(instance_name, i_id, fname, lname, email, phone, dummy_password))
					con.commit()
					cur.close()
					cur=con.cursor()
					cur.execute("INSERT INTO {}.INTERVIEWER VALUES ({}, {}, {}, '{}', '{}')".format(instance_name, i_id, 0, getVIPStatus(vip), class_schedule, role))
					con.commit()
					cur.close()
				interests = career_interests.strip().split(";")
				print ("Adding interests")
				con = getConnection()
				cur=con.cursor()
				cur.execute("DELETE FROM {}.INT_MAPPING WHERE P_ID = {}".format(instance_name, i_id))
				con.commit()
				cur.close()
				for interest in interests:
					interest = getInterestNumber(interest)
					con = getConnection()
					cur=con.cursor()
					cur.execute("INSERT INTO {}.INT_MAPPING VALUES ({}, {})".format(instance_name, i_id, interest))
					con.commit()
					cur.close()

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
			result = getQueryResult(query, fetchTop=15)
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

@application.route('/pythonlogin/profile_student')
def profile_student():
	# Check if user is loggedin
	if 'loggedin' in session:
		# We need all the account info for the user so we can display it on the profile page
		con = getConnection()
		cur = con.cursor()
		print(session['id'])
		cur.execute('SELECT * FROM {}.PERSON WHERE P_ID = {}'.format(instance_name, session['id']))
		account = cur.fetchone()
		cur.close()
		# Show the profile page with account info
		interests = getUserInterests(session["id"])
		print ("-------")
		print (account)
		account = list(account)
		print (type(account))
		for interest in interests:
			print ("interest", interest)
			account.append(interest)
		account = tuple(account)
		print (account)
		return render_template('profile_student.html', account=account,data=[{'name':'Data Science'}, {'name':'Machine Learning'}, {'name':'Full-Stack Engineering'},{'name':'Data Engineering'},{'name':'Cloud Architect'},{'name':'Dev-Ops'}])


@application.route('/pythonlogin/profile_student',methods = ['POST', 'GET'])
def submit():
	if request.method == 'POST':
		con = getConnection()
		cur=con.cursor()
		cur.execute("DELETE FROM {}.INT_MAPPING WHERE P_ID = {}".format(instance_name, session["id"]))
		cur.execute("INSERT INTO {}.INT_MAPPING VALUES ({}, {})".format(instance_name, session["id"], getInterestId(request.form['interest_1'])))
		cur.execute("INSERT INTO {}.INT_MAPPING VALUES ({}, {})".format(instance_name, session["id"], getInterestId(request.form['interest_2'])))
		cur.execute("INSERT INTO {}.INT_MAPPING VALUES ({}, {})".format(instance_name, session["id"], getInterestId(request.form['interest_3'])))
		con.commit()
		cur.close()
		return redirect(url_for('home_student'))

@application.route('/pythonlogin/home_admin')
def home_admin():
	# Check if user is loggedin
	if isSession() and isAdmin():
		# User is loggedin show them the home page
		# return render_template('home_admin.html', username=getPersonName(session["id"]))
		return redirect(url_for('newevent'))
	# User is not loggedin redirect to login page
	return redirect(url_for('login'))

@application.route('/pythonlogin/profile_admin')
def profile_admin():
	# Check if user is loggedin
	if isSession() and isAdmin():
		# We need all the account info for the user so we can display it on the profile page
		con = getConnection()
		cur = con.cursor()
		print(session['id'])
		cur.execute('SELECT * FROM {}.PERSON WHERE P_ID = {}'.format(instance_name, session['id']))
		account = cur.fetchone()
		cur.close()
		# Show the profile page with account info
		return render_template('profile_admin.html', account=account)

if __name__ == "__main__":
	application.run(debug=True)


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

# ajith/pooja

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users









# @app.route('/pythonlogin/profile_admin')
# def profile_admin():
# 	# Check if user is loggedin
# 	if 'loggedin' in session:
# 		# We need all the account info for the user so we can display it on the profile page
# 		cur = con.cursor()
# 		print(session['id'])
# 		cur.execute('SELECT * FROM admin_info WHERE id = %s', (session['id'],))
# 		account = cur.fetchone()
# 		cur.close()
# 		# Show the profile page with account info
# 		return render_template('profile_admin.html', account=account )
# ​
# @app.route('/pythonlogin/profile_student',methods = ['POST', 'GET'])
# def submit():
# 	if request.method == 'POST':
# 		cur=con.cursor()
# 		interest_1=request.form['interest_1']
# 		interest_2=request.form['interest_2']
# 		interest_3=request.form['interest_3']
# 		cur.execute('UPDATE student_info SET interest_1=%s,interest_2=%s,interest_3=%s WHERE id = %s' ,(interest_1,interest_2,interest_3,session['id']))
# 		con.commit()
# 		cur.close()
# ​
# # User is not loggedin redirect to login page
# return redirect(url_for('home_student'))
# @app.route('/pythonlogin/profile_interviewer')
# def profile_interviewer():
# 	# Check if user is loggedin
# 	if 'loggedin' in session:
# 		# We need all the account info for the user so we can display it on the profile page
# 		cur = con.cursor()
# 		cur.execute('SELECT * FROM interviewer_info WHERE id = %s', (session['id'],))
# 		account = cur.fetchone()
# 		cur.close()
# 		# Show the profile page with account info
# 		return render_template('profile_interviewer.html', account=account,data=[{'name':'Data Science'}, {'name':'Machine Learning'}, {'name':'Full-Stack Engineering'},{'name':'Data Engineering'},{'name':'Cloud Architect'},{'name':'Dev-Ops'}])
# @app.route('/pythonlogin/profile_interviewer',methods = ['POST', 'GET'])
# def submit_interviewer():
# 	if request.method == 'POST':
# 		cur=con.cursor()
# 		interest_1=request.form['interest_1']
# 		interest_2=request.form['interest_2']
# 		interest_3=request.form['interest_3']
# 		cur.execute('UPDATE interviewer_info SET interest_1=%s,interest_2=%s,interest_3=%s WHERE id = %s' ,(interest_1,interest_2,interest_3,session['id']))
# 		con.commit()
# 		cur.close()
# 	return redirect(url_for('home_interviewer'))
# @app.route('/pythonlogin/jobupdate',methods = ['POST', 'GET'])
# def submit_job():
# 	if request.method == 'POST':
# 		cur=con.cursor()
# 		organization=request.form['organization']
# 		job_position=request.form['job_position']
#
# 		cur.execute('UPDATE interviewer_info SET organization=%s,job_position=%s WHERE interviewer_id = %s' ,(organization,job_position,session['id']))
# 		con.commit()
# 		cur.close()
# 	return redirect(url_for('home_interviewer'))
# @app.route('/pythonlogin/home_interviewer')
# def home_interviewer():
# 	# Check if user is loggedin
# 	if 'loggedin' in session:
# 		# User is loggedin show them the home page
# 		return render_template('home_interviewer.html', username=session['username'])
# 	# User is not loggedin redirect to login page
# 	return redirect(url_for('login'))
