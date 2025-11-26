import sqlite3
import os
import json
import requests
import hashlib
import hmac
import base64
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)

#search here

userURL = "http://users-container:5000/"
docURL = "http://documents-container:5001/"
logURL = "http://logging-container:5003/"

'''
Helper functions
'''
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
End points
'''

@app.route('/clear', methods=(['GET']))
def clear():

	return "No database to clear"

@app.route('/search', methods=(['GET']))
def search():
	filename = request.args.get('filename')

	if not filename:
		return {"status": 2, "data":"NULL"}

	jwt = request.headers.get('Authorization')
	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status": 2})
	payload = decodedJWT["data"]
	uname = payload.get("username")

	userURLgroup = userURL + 'get_group'
	userRequest = requests.post(url=userURLgroup, headers={'Authorization': jwt})
	userGroup = userRequest.json().get('group')

	searchData = {"filename": filename,}

	docURLdata = docURL + 'get_data'
	docRequest = requests.post(url=docURLdata, headers={'Authorization': jwt}, data={"filename":filename})
	docData = docRequest.json()
	docGroups = docData["groups"]
	docHash = docData["hash"]
	docOwner = docData["creator"]

	searchData["owner"] = docOwner

	logURLdata = logURL + 'get_data'
	logRequest = requests.post(url=logURLdata, headers={'Authorization': jwt}, data={"filename":filename})
	logData = logRequest.json()
	logLast = logData["last_mod"]
	logTotal = logData["total_mod"]

	searchData["last_mod"] = logLast
	searchData["total_mod"] = logTotal
	searchData["hash"] = docHash

	if userGroup not in docGroups:
		print("user group no in doc groups")
		return {"status": 3, "data": "NULL"}

	print("to log:")

	if uname and filename:
		logURLdoc = logURL +"document_search"
		params={"filename": filename,
				"username": uname}
		print(params)
		log = requests.post(url=logURLdoc, params=params)
	elif uname:
		logURLdoc = logURL +"document_search"
		params={"username": uname}
		print(params)
		log = requests.post(url=logURLdoc, params=params)
	return {"status": 1, "data":searchData}


@app.route('/', methods=(['GET']))
def index():

	return json.dumps({'1': 'test', '2': 'test2'})

@app.route('/test_micro', methods=(['GET']))
def test_micro():

	return json.dumps({"response": "This is a message from Search Microservice"})

