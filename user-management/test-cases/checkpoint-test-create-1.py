import requests
import json
 
URLclear = "http://127.0.0.1:5000/clear"
r_clear = requests.get(url = URLclear)

URL = "http://127.0.0.1:5000/create_user"
PARAMS = {'first_name': 'James', 'last_name': 'Mariani', 'username': 'james.mariani', 'email_address': 'james@mariani.com', 'password': 'Examplepassword1', 'salt': 'FE8x1gO+7z0B'}

r = requests.post(url = URL, data = PARAMS)
data = r.json()

print(data)

f = open('test-create-1-solution.txt', 'r')
solution = json.loads(f.read())

print(solution)


for key in solution:
	if solution[key] != data[key]:
		print('Test Failed')
		quit()
		
print('Test Passed')
