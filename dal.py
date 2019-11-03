import pymysql
import configparser
import smtplib, ssl

# setting up configurations and constants
config = configparser.ConfigParser()
config.read('config.ini')

rds_host = config['RDS']['RDSHost']
rds_name = config['RDS']['RDSName']
rds_password = config['RDS']['RDSPassword']
db_name = config['RDS']['DBName']
instance_name = config['RDS']['InstanceName']

def getConnection():
  con = pymysql.connect(rds_host, user=rds_name, passwd=rds_password, db=db_name ,connect_timeout=5)
  return con


def getQueryResult(query, fetchOne=False, fetchTop=0):
  con = getConnection()
  cur = con.cursor()
  cur.execute(query)
  if fetchOne: return cur.fetchone()
  if fetchTop: return cur.fetchmany()
  else: return cur.fetchall()


def getPersonName(p_id):
  query = 'SELECT CONCAT(P_FNAME, " ", P_LNAME) FROM {}.PERSON WHERE P_ID = {}'.format(instance_name, p_id)
  result = getQueryResult(query, fetchOne=True)
  return result[0]



def getPersonType(p_id):
  query = "SELECT P_TYPE FROM {}.PERSON WHERE P_ID = {}".format(instance_name, p_id)
  result = getQueryResult(query, fetchOne=True)
  return result[0]


def getPersonInterests(p_id, get_names=False):
  if get_names:
    query = "SELECT I_NAME FROM {0}.INTERESTS WHERE I_ID IN (SELECT I_ID FROM {0}.INT_MAPPING WHERE P_ID = {1})" \
      .format(instance_name, p_id)
  else:
    query = "SELECT I_ID FROM {0}.INT_MAPPING WHERE P_ID = {1}".format(instance_name, p_id)

  result = getQueryResult(query)
  interests = list()
  for item in result:
    interests.append(item[0])
  return interests


def getPeopleFromEvent(event_id):
  query = 'SELECT P_ID FROM {0}.RSVP WHERE E_ID = {1}'.format(instance_name, event_id)
  result = getQueryResult(query)

  students = dict()
  interviewers = dict()
  for item in result:
    p_type = getPersonType(item[0])
    if p_type == 1:
      students[item[0]] = getPersonInterests(item[0])
    if p_type == 2:
      interviewers[item[0]] = getPersonInterests(item[0])

  return students, interviewers


def getInterestsList():
  query = 'SELECT DISTINCT I_NAME FROM {}.INTERESTS'.format(instance_name)
  result = getQueryResult(query)
  interests = [interest[0] for interest in result]
  return interests

def settMatch(i_id, s_id, start_time, end_time, event_id):
  con = getConnection()
  cur=con.cursor()
  cur.execute("INSERT INTO {}.MATCHES VALUES ({}, {}, {}, STR_TO_DATE('{}', '%H%i'), STR_TO_DATE('{}', '%H%i'))".format(instance_name, event_id, s_id, i_id, start_time, end_time))
  con.commit()
  cur.close()


def getInterestNumber(interest):
  try:
    I_ID = getQueryResult("SELECT I_ID FROM {}.INTERESTS WHERE I_NAME = '{}'".format(instance_name, interest), fetchOne=True)[0]
    return I_ID + 1
  except TypeError:
    I_ID = getQueryResult('SELECT MAX(I_ID) from {}.INTERESTS'.format(instance_name), fetchOne=True)[0]
    con = getConnection()
    cur=con.cursor()
    cur.execute("INSERT INTO {}.INTERESTS VALUES ({}, '{}')".format(instance_name, I_ID + 1, interest))
    con.commit()
    cur.close()
    return I_ID + 1


def getVIPStatus(s):
  if s == "True":
    return 1
  else:
    return 0

def mailTrigger(receiver, body):
  port = 587
  smtp_server = "smtp.gmail.com"
  sender_email = 'bgurram52@gmail.com'
  receiver_email = receiver
  password = 'Aseem@13'
  message = body
  context = ssl.create_default_context()
  with smtplib.SMTP(smtp_server, port) as server:
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)

print(getPeopleFromEvent(1))
print("Person Type: ", getPersonType(1))
print("Person Name: ", getPersonName(1))
print(getInterestsList())
a = getQueryResult('SELECT MAX(P_ID) from {}.PERSON WHERE P_TYPE = 11'.format(instance_name), fetchOne=True)
print ("A", a[0])
students = getQueryResult("SELECT P_EMAIL FROM {}.PERSON WHERE P_TYPE=1".format(instance_name))
for student_email in students:
  print (student_email[0])
# mailTrigger('abhishekmsharma@hotmail.com', "SUBJECT: Subject Line \n \n\nTest message")




