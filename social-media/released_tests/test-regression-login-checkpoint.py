import requests
import json

URLclear = "http://127.0.0.1:5000/clear"
r_clear = requests.get(url = URLclear)
 
URL = "http://127.0.0.1:5000/create_user"
PARAMS = {'first_name': 'James', 'last_name': 'Mariani', 'username': 'james.mariani', 'email_address': 'james@mariani.com', 'password': 'Examplepassword1', 'moderator': False, 'salt': 'FE8x1gO+7z0B'}

r = requests.post(url = URL, data = PARAMS)
data = r.json()

URLLogin = "http://127.0.0.1:5000/login"
LOGINPARAMS = {'username': 'james.mariani', 'password': 'Examplepassword1'}

r_login = requests.post(url = URLLogin, data = LOGINPARAMS)
login_data = r_login.json()

solution = {"status": 1, "jwt": "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJqYW1lcy5tYXJpYW5pIiwgImFjY2VzcyI6ICJUcnVlIn0=.e4d6e529e675f2bdd363da4c50219317375b7cc7d49da91083d1f0f09044ff89"}
	
for key in solution:
	if solution[key] != login_data[key]:
		print('Test Failed')
		quit()
print('Test Passed')
