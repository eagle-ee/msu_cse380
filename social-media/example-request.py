import requests
 
URL = "http://127.0.0.1:5000/test_get"
numbers = "3452"
PARAMS = {'numbers':numbers}
r = requests.get(url = URL, params = PARAMS)
#switch to this line below to test a post request... also change the URL endpoint above
#r = requests.post(url = URL, data = PARAMS)
data = r.json()
print(data)


URL = 'http://127.0.0.1:500/create_user'
params = 
r = requests.get(url=URL, params=PARAMS)
data = r.json()
print(data)