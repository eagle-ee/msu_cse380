import sqlite3
import os
import json
import requests
import hashlib
import base64
import hmac
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)

#document managment here

db_name = "documents.db"
sql_file = "documents.sql"
db_flag = False

userURL = "http://users-container:5000/"
searchURL = "http://search-container:5002/"
logURL = "http://logging-container:5003/"

'''
Helper functions
'''
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

def getUserGroup(jwt):
	url = "http://users-container:5000/get_group"
	headers = {'Authorization': jwt}

	try:
		response = requests.post(url, headers=headers)
		return response.json()
	except Exception:
		return {"status":2}

'''
End points
'''
@app.route('/clear', methods=(['GET']))
def clear():
	for rule in app.url_map.iter_rules():
		print(rule)
	print("out")
	conn = sqlite3.connect(db_name)

	with open(sql_file, 'r') as sql_startup:
		init_db = sql_startup.read()
	cursor = conn.cursor()
	cursor.executescript(init_db)
	conn.commit()
	
	return "Clear success"

@app.route('/create_document', methods=['POST'])
def create_document():
	jwt = request.headers.get('Authorization')

	if not jwt:
		return {"status": 2}
	decodedJWT = jsonDecode(jwt, p=True)
	print(type(decodedJWT))
	if decodedJWT.get("status") != 1:
		return {"status": 2}
	payload = decodedJWT["data"]
	uname = payload.get("username")

	filename = request.form.get('filename')
	body = request.form.get('body')
	groups = request.form.get('groups')

	if not filename or not body or not groups:
		return json.dumps({"status": 2})

	try:
		groupDict = json.loads(groups) if groups else {}
	except json.JSONDecodeError:
		return json.dumps({"status": 2})

	conn = get_db()
	cursor = conn.cursor()
	cursor.execute("PRAGMA foreign_keys = ON;")
	cursor.execute("DELETE FROM files WHERE filename = ?", (filename,))
	conn.commit()

	cursor.execute("INSERT INTO files(creator, filename) VALUES (?, ?);", (uname, filename))
	file_id = cursor.lastrowid

	for group in groupDict.values():
		cursor.execute("INSERT INTO file_groups(id, groupname) VALUES (?, ?)", (file_id, group))

	try:
		with open(filename, 'w', newline='\n') as file:
			file.write(body)
	except Exception:
		return json.dumps({"status": 2})

	conn.commit()
	conn.close()

	logURLdoc = logURL + "document_creation"
	params = {"filename": filename,
			  "username": uname}

	log = requests.post(url=logURLdoc, params=params)
	return json.dumps({"status": 1})

	#parse groups
	#insert into groups:
	#>Fetch id of stored file
	#>insert into file_groups at id, group (loop)
	#create file, or overwrite existing file
	#insert body into file

@app.route('/edit_document', methods=['POST'])
def edit_document():
	#check jwt
	#  >return 2 if bad jwt
	#validate user access via group
	# >http request to users (build document return function)
	# >return 3 if no access
	#edit document
	# >append to end of document
	jwt = request.headers.get('Authorization')
	if not jwt:
		return json.dump({"status": 2})
	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return {"status": 2, "data": "jwt"}
	payload = decodedJWT["data"]
	uname = payload.get("username")

	filename = request.form.get('filename')
	body = request.form.get('body')

	if not filename or not body:
		return json.dumps({"status": 2, "data": "no filename or body"})
	userGroup = getUserGroup(jwt)
	print(userGroup)
	if userGroup.get("status") != 1:
		return json.dumps({"status":2, "data":"invalid user group"})

	userGroupName = userGroup["group"]

	conn = get_db()
	cursor = conn.cursor()
	cursor.execute("SELECT groupname FROM files JOIN file_groups ON files.id = file_groups.id WHERE files.filename = ?", (filename,))
	fileGroups = cursor.fetchall()

	allowed = {group[0] for group in fileGroups}
	if userGroupName not in allowed:
		conn.close()
		return json.dumps({"status": 3})

	try:
		with open(filename, 'a', newline='\n') as file:
			file.write(body)
	except Exception:
		return json.dumps({"status": 2, "data":"couldnt open file"})

	conn.close()

	logURLdoc = logURL + "document_edit"
	params = {"filename": filename,
			  "username": uname}

	log = requests.post(url=logURLdoc, params=params)
	return json.dumps({"status": 1})

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
		return {"status":2}

	print(filename)
	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT id, creator FROM files WHERE filename = ?", (filename,))

	id, creator = cursor.fetchone()
	print(id)
	print(creator)
	print(filename)

	cursor.execute("SELECT groupname FROM file_groups WHERE id = ?", (id,))
	fileGroups = cursor.fetchall()
	print(fileGroups)
	retFileGroups = [group[0] for group in fileGroups]
	print(retFileGroups)

	try:
		with open(filename, 'rb') as file:
			hash = hashlib.file_digest(file, "sha256")
	except FileNotFoundError:
		return {"status": 2}

	return {"creator": creator,
			"groups": retFileGroups,
			"hash": hash.hexdigest()}







@app.route('/', methods=(['GET']))
def index():

	return json.dumps({'1': 'test', '2': 'test docs'})

@app.route('/test_micro', methods=(['GET']))
def test_micro():

	return json.dumps({"response": "This is a message from Document Microservice"})

