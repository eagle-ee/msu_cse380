import requests
import json
 
URLclear = "http://127.0.0.1:5000/clear"
r_clear = requests.get(url = URLclear)

URL = "http://127.0.0.1:5000/create_user"
PARAMS = {'first_name': 'James', 'last_name': 'Mariani', 'username': 'james.mariani', 'email_address': 'james@mariani.com', 'password': 'examplepassword1', 'salt': '4ErH1inwG6dJW0cu'}

r = requests.post(url = URL, data = PARAMS)
data = r.json()

f = open('test-create-2-solution.txt', 'r')
solution = json.loads(f.read())

for key in solution:
	if solution[key] != data[key]:
		print('Test Failed')
		quit()
		
print('Test Passed')
