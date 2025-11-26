import requests
import json

URLclear = "http://127.0.0.1:5000/clear"
r_clear = requests.get(url = URLclear)
 
URL = "http://127.0.0.1:5000/create_user"
PARAMS = {'first_name': 'James', 'last_name': 'Mariani', 'username': 'james.mariani', 'email_address': 'james@mariani.com', 'password': 'Examplepassword1', 'salt': 'FE8x1gO+7z0B'}

r = requests.post(url = URL, data = PARAMS)
data = r.json()
print(data)

URLLogin = "http://127.0.0.1:5000/login"
LOGINPARAMS = {'username': 'james.mariani', 'password': 'Examplepassword1'}

r_login = requests.post(url = URLLogin, data = LOGINPARAMS)
login_data = r_login.json()

f = open('test-login-solution.txt', 'r')
solution = json.loads(f.read())


print(solution["status"], solution['jwt'])
print(login_data["jwt"])

for key in solution:
	if solution[key] != login_data[key]:
		print('Test Failed')
		quit()
print('Test Passed')
