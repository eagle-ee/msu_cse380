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

#Build user management here

db_name = "user.db"
sql_file = "user.sql"
db_flag = False

docURL = "http://documents-container:5001/"
searchURL = "http://search-container:5002/"
logURL = "http://logging-container:5003/"

'''
Helper Functions
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


def checkPass(uname, pword, first, last):
    '''
    Check password requirements
    '''
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
    if (first.lower() in pword.lower()) or (last.lower() in pword.lower()) or (uname.lower() in pword.lower()):
        return False
    return True

def generateJWT(username):
    """
    Generate JWT using base64 safe encoding
    """
    header = json.dumps({"alg":"HS256", "typ" : "JWT"})
    payload = json.dumps({"username":username})

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
            return {"status": 2, "data":"NULL", 'test':'signature problem'}
        return {"status": 1, "data": payloadDict if p else "NULL"} #fallthrough success

    except:
        return {"status": 2, "data" : "NULL", 'test': 'try exception'}


'''
Endpoints
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

@app.route('/verify', methods=['POST'])
def verify():
    jwt = request.headers.get('Authorization')
    ret = jsonDecode(jwt, True)
    return ret.get('data')

@app.route('/create_user', methods=['POST'])
def create_user():
    first = request.form.get('first_name')
    last = request.form.get('last_name')
    uname = request.form.get('username')
    email = request.form.get('email_address')
    group = request.form.get('group')
    pword = request.form.get('password')
    salt = request.form.get('salt')

    if not all([first, last, uname, email, pword, salt]):
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

    hash = hashlib.sha256((pword + salt).encode()).hexdigest()

    cursor.execute("""INSERT INTO users (username, first_name, last_name, email_address, group_name, password, salt)
                   VALUES (?,?,?,?,?,?,?);""", (uname, first, last, email, group, hash, salt))

    user_id = cursor.lastrowid

    cursor.execute("INSERT INTO password_history(user_id, password) VALUES(?,?);", (user_id, hash))
    conn.commit()
    conn.close()

    logURLdoc = logURL + "user_creation"
    timestamp = datetime.now()
    params = {"username": uname}
    log = requests.post(url=logURLdoc, params=params)
    return json.dumps({"status": 1, "pass_hash": hash})

@app.route('/login', methods=['POST'])
def login():
    uname = request.form.get("username")
    pword = request.form.get("password")

    # check fields
    if not all([uname, pword]):
        return json.dumps({"status": 2, "jwt": "NULL"})

    # extract password
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password, salt FROM users WHERE username = ?;", (uname,))
    user = cursor.fetchone()

    if user is None:
        conn.close()
        return json.dumps({"status": 2, "jwt": "NULL"})

    storedHash, salt = user

    hash = hashlib.sha256((pword + salt).encode()).hexdigest()

    if hash != storedHash:
        conn.close()
        return json.dumps({"status": 2, "jwt": "NULL"})

    jwt = generateJWT(uname)
    conn.close()

    logURLdoc = logURL + "login"
    timestamp = datetime.now()
    params = {"username": uname}
    log = requests.post(url=logURLdoc, params=params)
    return json.dumps({"status": 1, "jwt": jwt})


@app.route('/update', methods=['POST'])
def update():
    uname = request.form.get('username')
    unameNew = request.form.get('new_username')
    pword = request.form.get('password')
    pwordNew = request.form.get('new_password')
    jwt = request.form.get('jwt')

    # validate jwt
    try:
        header, payload, signature = jwt.split('.')
        decodedHead = base64.urlsafe_b64decode(header + "==").decode('utf-8')
        decodedPayload = base64.urlsafe_b64decode(payload + "==").decode('utf-8')
        payloadDict = json.loads(decodedPayload)

        jwtUname = payloadDict.get("username")  # store uname for password change

        with open('key.txt', 'r') as key:
            signatureKey = key.read().strip()
        checkSig = hmac.new(signatureKey.encode('utf-8'), f'{header}.{payload}'.encode('utf-8'),
                            hashlib.sha256).hexdigest()

        if checkSig != signature:
            return json.dumps({"status": 3})
    except Exception:
        return json.dumps({"status": 3})

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE username = ?", (jwtUname,))
    user = cursor.fetchone()
    if user is None:
        conn.close()
        return json.dumps({"status": 2})
    user_id = user[0]

    if unameNew:
        # current uname exists
        cursor.execute("SELECT * FROM users WHERE username = ?;", (uname,))
        if cursor.fetchone() is None:
            conn.close()
            return json.dumps({"status": 2})
        # new uname unique
        cursor.execute("SELECT * FROM users WHERE username = ?;", (unameNew,))
        if cursor.fetchone() is not None:
            conn.close()
            return json.dumps({"status": 2})
        # otherwise update
        cursor.execute("UPDATE users SET username = ? WHERE username = ?;", (unameNew, uname))

        conn.commit()
        conn.close()
        return json.dumps({"status": 1})

    elif pwordNew:
        # current pword correct
        cursor.execute("SELECT password, salt, first_name, last_name FROM users WHERE username = ?;", (jwtUname,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return json.dumps({"status": 2, "test": "no user", "jwtUname": jwtUname})

        storedHash, salt, fname, lname = user
        hash = hashlib.sha256((pword + salt).encode()).hexdigest()
        if storedHash != hash:
            conn.close()
            return json.dumps({"status": 2, "test": "hash failure"})

        if not checkPass(jwtUname, pwordNew, fname, lname):
            conn.close()
            return json.dumps({"status": 2, "test": "bad pass"})

        cursor.execute("SELECT password FROM password_history WHERE user_id = ?", (user_id,))
        userPassHistory = cursor.fetchall()
        for oldPass in userPassHistory:
            if hashlib.sha256((pwordNew + salt).encode()).hexdigest() == oldPass[0]:
                conn.close()
                return json.dumps({"status": 2, "test": "old and new mismatch"})

        newHash = hashlib.sha256((pwordNew + salt).encode()).hexdigest()
        cursor.execute("INSERT INTO password_history (user_id, password) VALUES (?,?);", (jwtUname, newHash))
        cursor.execute("UPDATE users SET password = ? WHERE username = ?;", (newHash, jwtUname))
        conn.commit()
        conn.close()
        return json.dumps({"status": 1})


@app.route('/get_group', methods=['POST'])
def get_group():
    jwt = request.headers.get('Authorization')
    if not jwt:
        return json.dumps({"status": 2, "group": "NULL"})

    decodedJWT = jsonDecode(jwt, p=True)
    if decodedJWT['status'] != 1:
        return json.dumps({"status": 2, "group": "NULL"})
    username = decodedJWT["data"].get("username")

    if not username:
        return json.dumps({"status": 2, "group": "NULL"})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM users WHERE username = ?;", (username,))
    userGroup = cursor.fetchone()
    conn.close()

    if not userGroup:
        return json.dumps({"status": 2, "group": "NULL"})

    return json.dumps({"status": 1, "group": userGroup[0]})


@app.route('/', methods=(['GET']))
def index():
    MICRO2URL = "http://documents-container:5001/test_micro" #documents
    MICRO3URL = "http://search-container:5002/test_micro" #searching
    MICRO4URL = "http://logging-container:5003/test_micro" #logging
    r = requests.get(url = MICRO2URL)
    r2 = requests.get(url = MICRO3URL)
    r3 = requests.get(url = MICRO4URL)
    print(r.json())
    print(r2.json())
    print(r3.json())

    data = r.json()

    return data


@app.route('/test_micro', methods=(['GET']))
def test_micro():

    return "This is Microservice 1"
