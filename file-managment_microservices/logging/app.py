import sqlite3
import os
import json
import requests
import hashlib
import hmac
import base64
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

#logging here

db_name = "log.db"
sql_file = "log.sql"
db_flag = False

userURL = "http://users-container:5000/"
docURL = "http://documents-container:5001/"
searchURL = "http://search-container:5002/"

def create_db():
	conn = sqlite3.connect(db_name)

	with open(sql_file, 'r') as sql_startup:
		init_db = sql_startup.read()
	cursor = conn.cursor()
	cursor.executescript(init_db)
	conn.commit()
	conn.close()
	global db_flag
	db_flag = True
	return conn


def get_db():
	if not db_flag:
		create_db()
	conn = sqlite3.connect(db_name)
	return conn

def jsonDecode(jwt, p=False):
	try:
		header, payload, signature = jwt.split('.')
		decodedHead = base64.urlsafe_b64decode(header + "==").decode('utf-8')
		decodedPayload = base64.urlsafe_b64decode(payload + "==").decode('utf-8')
		payloadDict = json.loads(decodedPayload)

		with open('key.txt', 'r') as key:
			signatureKey = key.read().strip()
		checkSig = hmac.new(signatureKey.encode('utf-8'), f'{header}.{payload}'.encode('utf-8'),
							hashlib.sha256).hexdigest()
		if checkSig != signature:
			return {"status": 2, "data":"NULL", 'test':'signature problem'}
		return {"status": 1, "data": payloadDict if p else "NULL"} #fallthrough success

	except:
		return {"status": 2, "data" : "NULL", 'test': 'try exception'}



'''
End Points
'''
@app.route('/clear', methods=(['GET']))
def clear():
	conn = sqlite3.connect(db_name)

	with open(sql_file, 'r') as sql_startup:
		init_db = sql_startup.read()
	cursor = conn.cursor()
	cursor.executescript(init_db)
	conn.commit()
	return "Clear success"

@app.route('/get_data', methods=['POST'])
def get_data():
	jwt = request.headers.get('Authorization')
	if not jwt:
		return json.dump({"status": 2})
	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return {"status": 2}
	payload = decodedJWT["data"]
	uname = payload.get("username")

	filename = request.form.get("filename")
	if not filename:
		return {"status": 2}

	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT f.id FROM file_events AS f JOIN events AS e ON e.id = f.id WHERE filename = ? ORDER BY e.timestamp DESC;", (filename,))
	id = cursor.fetchone()[0]
	print(id)

	cursor.execute("SELECT username, event FROM events WHERE id=? ORDER BY timestamp DESC;",
				   (id,))
	lastModifier, lastEvent = cursor.fetchone()

	cursor.execute("SELECT COUNT(*) FROM events AS e JOIN file_events AS f ON e.id = f.id WHERE f.filename = ? AND e.event IN (?,?);",
				   (filename, "document_creation", "document_edit"))
	totalMods = cursor.fetchone()[0]

	return {"last_mod": lastModifier, "total_mod": totalMods}





@app.route('/view_log', methods=['GET'])
def view_log():
	jwt = request.headers.get('Authorization')
	username = request.args.get('username')
	filename = request.args.get('filename')

	if not jwt:
		return {"status":2, "data":"NULL"}
	decodedJWT = jsonDecode(jwt, True)
	if decodedJWT["status"] != 1:
		return {"status":2, "data":"NULL"}

	viewer = decodedJWT["data"].get("username")

	conn = get_db()
	cursor = conn.cursor()

	#try block:
	if username:
		if viewer != username:
			return {"status": 3, "data": "NULL"}
		cursor.execute("SELECT id, event, timestamp FROM events WHERE username = ? ORDER BY timestamp ASC;",
					   (username,))
	elif filename:
		userURLgroup = userURL + 'get_group'
		userRequest = requests.post(url=userURLgroup, headers={'Authorization':jwt})
		userGroup = userRequest.json().get('group')

		docURLgroup = docURL + 'get_data'
		docRequest = requests.post(url=docURLgroup, headers={'Authorization':jwt}, data={"filename":filename})
		docData = docRequest.json()
		docGroups = docData['groups']

		if userGroup not in docGroups:
			return {"status": 3, "data": "NULL"}

		cursor.execute("""SELECT e.id, e.event, e.username, f.filename, e.timestamp
		FROM events AS e
		JOIN file_events AS f ON f.id = e.id
		WHERE f.filename = ?
		ORDER BY e.timestamp ASC;""", (filename,))
	else:
		return {"status":3, "data":"NULL"}

	logs = cursor.fetchall()
	logData = {}
	for index, log in enumerate(logs, start=1):
		logData[index] = {
			"event" : log[1],
			"user" : log[2],
			"filename" : log[3] if filename else "NULL",
		}

	conn.close()
	return {"status":1, "data":logData}


@app.route('/user_creation', methods=['POST'])
def user_creation():
	username = request.args.get('username')
	if username:
		conn = get_db()
		cursor = conn.cursor()

		timestamp = datetime.now()

		cursor.execute("INSERT INTO events(username, event, timestamp) VALUES(?, ?, ?);", (username, "user_creation", timestamp))
		conn.commit()

		conn.close()
		return {"status": "success"}, 200
	return {"status":"failure", "error":"no username"}, 400

@app.route('/login', methods=['POST'])
def log_login():
	username = request.args.get('username')
	if username:
		conn = get_db()
		cursor = conn.cursor()

		timestamp = datetime.now()

		cursor.execute("INSERT INTO events(username, event, timestamp) VALUES (?,?,?);", (username, "login", timestamp))
		conn.commit()

		conn.close()
		return {"status": "success"}, 200
	return {"status": "failure", "error":"no username"}, 400

@app.route('/document_creation', methods=['POST'])
def document_creation():
	username = request.args.get('username')
	filename = request.args.get('filename')

	if username and filename:
		conn = get_db()
		cursor = conn.cursor()

		timestamp = datetime.now()

		cursor.execute("INSERT INTO events(username, event, timestamp) VALUES (?,?,?);", (username, "document_creation", timestamp))
		id = cursor.lastrowid
		conn.commit()

		cursor.execute("INSERT INTO file_events(id, filename) VALUES (?,?);", (id, filename))
		conn.commit()

		conn.close()
		return {"status": "success"}, 200
	return {"status": "failure", "error":"no username"}, 400

@app.route('/document_edit', methods=['POST'])
def document_edit():
	username = request.args.get('username')
	filename = request.args.get('filename')
	if username and filename:
		conn = get_db()
		cursor = conn.cursor()

		timestamp = datetime.now()

		cursor.execute("INSERT INTO events(username, event, timestamp) VALUES (?,?,?);",
					   (username, "document_edit", timestamp))
		id = cursor.lastrowid
		conn.commit()

		cursor.execute("INSERT INTO file_events(id, filename) VALUES (?,?);", (id, filename))
		conn.commit()

		conn.close()
		return {"status": "success"}, 200
	return {"status": "failure", "error": "no username"}, 400

@app.route('/document_search', methods=['POST'])
def document_search():
	username = request.args.get('username')
	filename = request.args.get('filename')

	print(username)
	print(filename)

	if username:
		conn = get_db()
		cursor = conn.cursor()

		timestamp = datetime.now()

		cursor.execute("INSERT INTO events(username, event, timestamp) VALUES (?,?,?);",
					   (username, "document_search", timestamp))
		id = cursor.lastrowid
		conn.commit()

		if filename:
			cursor.execute("INSERT INTO file_events(id, filename) VALUES (?,?);", (id, filename))
			conn.commit()

		conn.close()
		return {"status": "success"}, 200
	return {"status": "failure", "error": "no username"}, 400


@app.route('/', methods=(['GET']))
def index():

	return json.dumps({'1': 'test', '2': 'test log'})

@app.route('/test_micro', methods=(['GET']))
def test_micro():

	return json.dumps({"response": "This is a message from Logging microservice"})

