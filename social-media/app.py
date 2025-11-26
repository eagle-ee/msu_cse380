import sqlite3
import os
from flask import Flask, request
import json
import hashlib
import base64
import hmac

app = Flask(__name__)
db_name = "project2.db"
sql_file = "project2.sql"
db_flag = False

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

@app.route('/', methods=(['GET']))
def index():
	conn = get_db()
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM test;")
	result = cursor.fetchall()
	conn.close()

	return result

@app.route('/clear', methods=(['GET']))
def clear():
	conn = sqlite3.connect(db_name)
	
	with open(sql_file, 'r') as sql_startup:
		init_db = sql_startup.read()
	cursor = conn.cursor()
	cursor.executescript(init_db)
	conn.commit()
	return "Clear success"



'''
Helper Functions
'''
def checkPass(uname, pword, first, last):
	"""
	Checks password requirements
	"""
	upCount = 0
	lowCount = 0
	numCount = 0
	totCount = len(pword)
	# check min password requirements
	for ch in pword:
		if ch.isalpha():
			if ch.isupper():
				upCount += 1
			else:
				lowCount += 1
		else:
			if ch.isdigit():
				numCount += 1
	# ***
	if (totCount < 8):
		return False
	elif (upCount < 1 or lowCount < 1 or numCount < 1):
		return False

	# check if first, last, or uname in password
	if (first in pword) or (last in pword) or (uname in pword):
		return False
	return True

def generateJWT(username, access, mod):
	"""
	Generate JWT using base64 safe encoding
	"""
	print(username)
	print(access)
	print(mod)
	print()
	header = json.dumps({"alg":"HS256", "typ" : "JWT"})
	if mod == "True":
		print("Paylod with mod")
		payload = json.dumps({"username":username, "access":str(access),"moderator":mod})
	else:
		print("payload no mod")
		payload = json.dumps({"username":username, "access": str(access)})

	with open('key.txt', 'r') as key:
		signatureKey = key.read().strip()

	def base64Encode(data):
		return base64.urlsafe_b64encode(data).decode('utf-8')

	print(payload)

	encodedHead = base64Encode(header.encode('utf-8'))
	encodedPayload = base64Encode(payload.encode('utf-8'))

	signature = hmac.new(signatureKey.encode('utf-8'), msg=(encodedHead+'.'+encodedPayload).encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
	print(encodedPayload)

	jwt = f"{encodedHead}.{encodedPayload}.{signature}"
	return jwt

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
			return json.dumps({"status": 2, "data":"NULL", 'test':'signature problem'})
		return {"status": 1, "data": payloadDict if p else "NULL"} #fallthrough success

	except:
		return json.dumps({"status": 2, "data" : "NULL", 'test': 'try exception'})

'''
End Points
'''
@app.route('/create_user', methods=['POST'])
def create_user():
	
	first = request.form.get('first_name')
	last = request.form.get('last_name')
	uname = request.form.get('username')
	email = request.form.get('email_address')
	pword = request.form.get('password')
	mod = request.form.get('moderator')
	salt = request.form.get('salt')

	print("***")




	if not all([first, last, uname, email, pword, mod, salt]):
		return json.dumps({"status": 4, "pass_hash": "NULL"})
	
	conn = get_db()
	cursor = conn.cursor()
	
	cursor.execute("SELECT * FROM users WHERE username = ?;", (uname,))
	if cursor.fetchone() is not None:
		conn.close()
		return json.dumps({"status": 2, "pass_hash": "NULL"})
	cursor.execute("SELECT * FROM users WHERE email_address = ?;", (email,))
	if cursor.fetchone() is not None:
		conn.close()
		return json.dumps({"status": 3, "pass_hash": "NULL"})
	if not checkPass(uname, pword, first, last):
		conn.close()
		return json.dumps({"status": 4, "pass_hash": "NULL"})
	
	hash = hashlib.sha256((pword+salt).encode()).hexdigest()
	
	cursor.execute("INSERT INTO users (username, first_name, last_name, email_address, password, moderator, salt)\
				   VALUES (?,?,?,?,?,?,?);", (uname, first, last, email, hash, mod, salt))

	user_id = cursor.lastrowid

	cursor.execute("INSERT INTO password_history(user_id, password) VALUES(?,?);", (user_id, hash))
	conn.commit()
	conn.close()
	return json.dumps({"status": 1, "pass_hash": hash})



@app.route('/login', methods=['POST'])
def login():
	uname = request.form.get("username")
	pword = request.form.get("password")
	mod = False

	#check fields
	if not all([uname, pword]):
		return json.dumps({"status": 2, "jwt":"NULL"})

	#extract password
	conn = get_db()
	cursor = conn.cursor()
	cursor.execute("SELECT password, moderator, salt FROM users WHERE username = ?;", (uname,))
	user = cursor.fetchone()

	if user is None:
		conn.close()
		return json.dumps({"status": 2, "jwt":"NULL"})

	storedHash, mod, salt = user

	hash = hashlib.sha256((pword+salt).encode()).hexdigest()

	if hash != storedHash:
		conn.close()
		return json.dumps({"status":2, "jwt":"NULL"})

	jwt = generateJWT(uname, True, mod) 
	conn.close()
	return json.dumps({"status":1, "jwt":jwt})

@app.route('/update', methods=['POST'])
def update():
	uname = request.form.get('username')
	unameNew = request.form.get('new_username')
	pword = request.form.get('password')
	pwordNew = request.form.get('new_password')
	jwt = request.form.get('jwt')

	if not jwt:
		return json.dumps({"status":2, "data":"NULL", 'test':'no jwt'})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status":3})
	payload = decodedJWT["data"]
	uname = payload.get("username")


	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT user_id FROM users WHERE username = ?", (jwtUname,))
	user = cursor.fetchone()
	if user is None:
		conn.close()
		return json.dumps({"status": 2})
	user_id = user[0]
	
	if unameNew:
		#current uname exists
		cursor.execute("SELECT * FROM users WHERE username = ?;", (uname,))
		if cursor.fetchone() is None:
			conn.close()
			return json.dumps({"status":2})
		#new uname unique
		cursor.execute("SELECT * FROM users WHERE username = ?;", (unameNew,))
		if cursor.fetchone() is not None:
			conn.close()
			return json.dumps({"status":2})
		#otherwise update
		cursor.execute("UPDATE users SET username = ? WHERE username = ?;", (unameNew, uname))
		
		conn.commit()
		conn.close()
		return json.dumps({"status":1})
	
	elif pwordNew:
		#current pword correct
		cursor.execute("SELECT password, salt, first_name, last_name FROM users WHERE username = ?;", (jwtUname,))
		user = cursor.fetchone()
		if not user:
			conn.close()
			return json.dumps({"status":2, "test":"no user", "jwtUname": jwtUname})
		
		storedHash, salt, fname, lname = user
		hash = hashlib.sha256((pword+salt).encode()).hexdigest()
		if storedHash != hash:
			conn.close()
			return json.dumps({"status":2, "test":"hash failure"})

		if not checkPass(jwtUname, pwordNew, fname, lname):
			conn.close()
			return json.dumps({"status":2, "test":"bad pass"})
		
		cursor.execute("SELECT password FROM password_history WHERE user_id = ?", (user_id,))
		userPassHistory = cursor.fetchall()
		for oldPass in userPassHistory:
			if hashlib.sha256((pwordNew+salt).encode()).hexdigest() == oldPass[0]:
				conn.close()
				return json.dumps({"status":2, "test":"old and new mismatch"})
		
		newHash = hashlib.sha256((pwordNew+salt).encode()).hexdigest()
		cursor.execute("INSERT INTO password_history (user_id, password) VALUES (?,?);", (jwtUname, newHash))
		cursor.execute("UPDATE users SET password = ? WHERE username = ?;", (newHash, jwtUname))
		conn.commit()
		conn.close()
		return json.dumps({"status":1})
				
@app.route('/view', methods=['POST'])
def view():
	jwt = request.form.get('jwt')

	if not jwt:
		return json.dumps({"status":2, "data":"NULL", 'test':'no jwt'})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status":2, "data":"NULL"})
	payload = decodedJWT["data"]
	uname = payload.get("username")

	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT first_name, last_name, email_address FROM users WHERE username = ?;", (uname,))
	conn.commit()
	user = cursor.fetchone()

	if user is None:
		conn.close()
		return json.dumps({"status": 2, "data":"NULL", 'test':'no user'})

	fname, lname, email = user

	conn.close()
	return json.dumps({"status" : 1, "data" : {"username" : uname,
										  "email_address" : email,
										  "first_name" : fname,
										  "last_name" : lname}
					   })

@app.route('/create_post', methods=(['POST']))
def create_post():
	jwt = request.headers.get('Authorization')

	if not jwt:
		return json.dumps({"status": 2, "data": "NULL", 'test': 'no jwt'})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status":2})
	payload = decodedJWT["data"]
	uname = payload.get("username")
	
	title = request.form.get('title')
	body = request.form.get('body')
	post_id = request.form.get('post_id')
	tagsStr = request.form.get('tags')
	
	if not title or not body or not post_id:
		return json.dumps({"stats":2})
	
	try:
		tags = json.loads(tagsStr) if tagsStr else {} #edit here
	except json.JSONDecodeError:
		return json.dumps({"status":2})
	
	conn = get_db()
	cursor = conn.cursor()
	
	cursor.execute("SELECT *FROM posts WHERE post_id = ?;", (post_id,))
	if cursor.fetchone() is not None:
		conn.close()
		return json.dumps({"status":2})

	cursor.execute("SELECT * FROM users WHERE username = ?;", (uname,))
	user = cursor.fetchone()

	if user is None:
		conn.close()
		return json.dumps({"status":2})
	user_id = user[0]
	
	cursor.execute("INSERT INTO posts (post_id, user_id, title, body) VALUES (?,?,?,?);", (post_id, user_id, title, body))
	for key, tag in tags.items():
		cursor.execute("INSERT INTO tags (post_id, tag) VALUES (?, ?);", (post_id, tag))
	
	conn.commit()
	conn.close()
	return json.dumps({"status":1})



@app.route('/like', methods=(['POST']))
def like():
	jwt = request.headers['Authorization']

	if not jwt:
		return json.dumps({"status":2, "test":"jwt invalid"})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status":2, "test":"decode failure"})
	payload = decodedJWT["data"]
	uname = payload.get("username")

	post_id = request.form.get('post_id')

	if not post_id:
		return json.dumps({"status":2, "test":"no post_id"})

	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT user_id FROM posts WHERE post_id = ?;", (post_id,))
	postOwner = cursor.fetchone()

	if postOwner is None:
		conn.close()
		return json.dumps({"status":2, "test":"no post owner"})

	cursor.execute("SELECT 1 FROM follows WHERE follower_id = (SELECT user_id FROM users"\
				   " WHERE username = ?) AND followed_id = ?;", (uname, postOwner[0]))
	isFollower = cursor.fetchone()

	if isFollower is None:
		conn.close()
		return json.dumps({"status":2, "test":"not following"})

	cursor.execute("SELECT 1 FROM likes WHERE user_id = (SELECT user_id frOM users"\
				   " WHERE username = ?) AND post_id = ?;", (uname, post_id))
	liked = cursor.fetchone()

	if liked is not None:
		conn.close()
		return json.dumps({"status":2, "test":"already liked"})

	cursor.execute("INSERT INTO likes (user_id, post_id) VALUES ((SELECT user_id FROM users WHERE "\
				   "username = ?), ?);", (uname, post_id))
	conn.commit()
	conn.close()

	return json.dumps({"status":1})

@app.route('/follow', methods=(['POST']))
def follow():
	jwt = request.headers['Authorization']

	if not jwt:
		return json.dumps({"status": 2})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status": 2})
	payload = decodedJWT["data"]
	uname = payload.get("username")

	unameFollowed = request.form.get('username')
	if not unameFollowed:
		return json.dumps({"status":2})

	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT user_id FROM users WHERE username = ?;", (uname,))
	user_id = cursor.fetchone()
	if user_id is None:
		conn.close()
		return json.dumps({"status":2})
	user_id = user_id[0]

	cursor.execute("SELECT user_id FROM users WHERE username = ?;", (unameFollowed,))
	followed_id = cursor.fetchone()
	if followed_id is None:
		conn.close()
		return json.dumps({"status":2})
	followed_id = followed_id[0]

	cursor.execute("INSERT INTO follows(follower_id, followed_id) VALUES (?,?);", (user_id, followed_id))

	conn.commit()
	conn.close()

	return json.dumps({"status":1})



@app.route('/view_post/<id>', methods=(['GET']))
def view_post(id):
	lookup = {}
	jwt = request.headers['Authorization']

	if not jwt:
		return json.dumps({"status":2, "data":"NULL","test":"no jwt"})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status": 2})
	payload = decodedJWT["data"]
	uname = payload.get("username")

	lookup['title'] = request.args.get('title')
	lookup['body'] = request.args.get('body')
	lookup['tags'] = request.args.get('tags')
	lookup['owner'] = request.args.get('owner')
	lookup['likes'] = request.args.get('likes')

	conn = get_db()
	cursor = conn.cursor()

	cursor.execute("SELECT users.username FROM posts INNER JOIN users ON posts.user_id"\
				   "= users.user_id WHERE posts.post_id = ?;", (id,))
	owner = cursor.fetchone()
	if not owner:
		conn.close()
		return json.dumps({"status":2, "data":"NULL","test":"post not found"})
	if uname != owner[0]:
		cursor.execute(
			"SELECT 1 FROM follows "
			"INNER JOIN users ON follows.followed_id = users.user_id "
			"WHERE users.username = ? AND follows.follower_id = "
			"(SELECT user_id FROM users WHERE username = ?);",
			(owner[0], uname)
		)
		if not cursor.fetchone():
			conn.close()
			return json.dumps({"status":2,"data":"NULL","test":"unathorized"})

	data={}
	if lookup.get("title") or lookup.get("body"):
		cursor.execute("SELECT title, body FROM posts WHERE post_id = ?;", (id,))
		post = cursor.fetchone()
		if post:
			if lookup.get('title'):
				data['title'] = post[0]
			if lookup.get('body'):
				data['body'] = post[1]
	if lookup.get('tags'):
		cursor.execute("SELECT tag FROM tags WHERE post_id = ?;", (id,))
		tags = cursor.fetchall()
		data['tags'] = [tag[0] for tag in tags] if tags else []
	if lookup.get('owner'):
		data['owner'] = owner[0]
	if lookup.get('likes'):
		cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?;", (id,))
		likes = cursor.fetchone()[0]
		data["likes"] = likes

	conn.close()
	return json.dumps({"status":1, "data": data})

	conn.close()

@app.route('/search', methods=['GET'])
def search():
	jwt = request.headers['Authorization']

	if not jwt:
		return json.dumps({"status": 2, "data": "NULL", "test": "no jwt"})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status": 2})
	payload = decodedJWT["data"]
	uname = payload.get("username")

	conn = get_db()
	cursor = conn.cursor()

	feed = request.args.get('feed')
	tag = request.args.get('tag')

	data = {}

	if feed == "True":
		cursor.execute("""
		SELECT posts.post_id, posts.user_id, posts.title, posts.body, users.username FROM posts
		INNER JOIN follows ON posts.user_id = follows.followed_id
		INNER JOIN users ON posts.user_id = users.user_id
		WHERE follows.follower_id = (SELECT user_id FROM users WHERE username = ?)
		ORDER BY posts.post_id DESC LIMIT 5""", (uname,))
		posts = cursor.fetchall()

		for post in posts:
			post_id, user_id, title, body, owner = post

			cursor.execute("SELECT tag FROM tags WHERE post_id = ?;", (post_id,))
			tags = [row[0] for row in cursor.fetchall()]

			cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?;", (post_id,))
			likes = cursor.fetchone()[0]
			data[post_id] = {"title": title, "body": body, "tags":tags, "owner":owner, "likes":likes}
	elif tag:
		cursor.execute("""
		SELECT posts.post_id, posts.user_id, posts.title, posts.body users.username FROM posts
		INNER JOIN tags ON posts.post_id = tags.post_id
		INNER JOIN follows ON posts.user_id = follows.followed_id
		INNER JOIN users ON posts.user_id = users.user_id
		WHERE follows.follower_id = (SELECT user_id FROM users WHERE username = ?)
		AND tags.tag = ?
		ORDER BY posts.post_id DESC;""", (uname, tag))
		posts = cursor.fetchall()

		for post in posts:
			post_id, user_id, title, body, owner = post

			#edit
			cursor.execute("SELECT tag FROM tags WHERE post_id = ?;", (post_id,))
			tags = [row[0] for row in cursor.fetchall()]
			#end edit

			cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?;", (post_id,))
			likes = cursor.fetchone()[0]

			data[post_id] = {"title": title, "body": body, "tags": tags,"owner": owner, "likes": likes}

	conn.close()

	return json.dumps({"status": 1, "data": data})

@app.route('/delete', methods=['POST'])
def delete():
	jwt = request.headers['Authorization']

	if not jwt:
		return json.dumps({"status":2})

	decodedJWT = jsonDecode(jwt, p=True)
	if decodedJWT["status"] != 1:
		return json.dumps({"status":2})

	payload = decodedJWT['data']
	uname = payload.get("username")

	unameDelete = request.form.get('username')
	post_IDdelete = request.form.get('post_id')

	conn = get_db()
	cursor = conn.cursor()
	cursor.execute("PRAGMA foreign_keys = ON;")
	conn.commit();

	cursor.execute("SELECT moderator FROM users WHERE username = ?;", (uname,))
	mod = cursor.fetchone()[0]

	if unameDelete is not None:
		if uname != unameDelete:
			conn.close()
			return json.dumps({"status":2, "test": "unauthorized user"})
		cursor.execute("DELETE FROM users WHERE username = ?;", (unameDelete,))
		conn.commit()

	elif post_IDdelete is not None:
		cursor.execute("SELECT user_id FROM posts WHERE post_id = ?;", (post_IDdelete,))
		postOwner = cursor.fetchone()
		if postOwner is None:
			conn.close()
			return json.dumps({"status": 2})
		cursor.execute("SELECT user_id FROM users WHERE username = ?;", (uname,))
		requestID = cursor.fetchone()[0]

		if postOwner[0] != requestID and mod == "False":
			conn.close()
			return json.dumps({"status":2})

		cursor.execute("DELETE FROM posts WHERE post_id = ?;", (post_IDdelete,))
		conn.commit()
	else:
		conn.close()
		return json.dumps({"status":2})

	conn.close()
	return json.dumps({"status":1})




@app.route('/test_get/<post_id>', methods=(['GET', 'POST']))
def test_get(post_id):
	result = {}
	result['numbers'] = request.args.get('numbers')
	result['post_id'] = post_id
	result['jwt'] = request.headers['Authorization']

	return json.dumps(result)


@app.route('/test_post', methods=(['POST']))
def test_post():
	result = request.form

	return result