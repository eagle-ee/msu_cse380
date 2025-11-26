import requests
import json
 
URLclear = "http://127.0.0.1:5000/clear"
r_clear = requests.get(url = URLclear)
 
URL = "http://127.0.0.1:5000/create_user"
PARAMS = {'first_name': 'James', 'last_name': 'Mariani', 'username': 'james.mariani', 'email_address': 'james@mariani.com', 'password': 'Examplepassword1', 'salt': 'FE8x1gO+7z0B'}

r = requests.post(url = URL, data = PARAMS)
data = r.json()

URLLogin = "http://127.0.0.1:5000/login"
LOGINPARAMS = {'username': 'james.mariani', 'password': 'Examplepassword1'}

r_login = requests.post(url = URLLogin, data = LOGINPARAMS)
login_data = r_login.json()


URLEdit = "http://127.0.0.1:5000/update"
EDITPARAMS = {'username': 'james.mariani', 'new_username': 'mariani.james', 'jwt': login_data['jwt']}

r_edit = requests.post(url = URLEdit, data = EDITPARAMS)

LOGINPARAMS = {'username': 'mariani.james', 'password': 'Examplepassword1'}

r_login = requests.post(url = URLLogin, data = LOGINPARAMS)
login_data = r_login.json()

URLView = "http://127.0.0.1:5000/view"
VIEWPARAMS = {'jwt': login_data['jwt']}

r_view = requests.post(url = URLView, data = VIEWPARAMS)
view_data = r_view.json()

f = open('test-edit-solution.txt', 'r')
solution = json.loads(f.read())
	
for key in solution:
	if solution[key] != view_data[key]:
		print('Test Failed')
		quit()

print('Test Passed')
