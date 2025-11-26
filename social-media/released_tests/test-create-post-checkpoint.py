import requests
import json
import os

try:
	URLclear = "http://127.0.0.1:5000/clear"
	r_clear = requests.get(url = URLclear)
	
	URL = "http://127.0.0.1:5000/create_user"
	PARAMS = {'first_name': 'Harbaugh', 'last_name': 'IsACheater', 'username': 'cheater', 'email_address': 'jim@cheater.com', 'password': 'Iheartcheating1', 'moderator': True, 'salt': 'FE8x1gO+7z0B'}

	r = requests.post(url = URL, data = PARAMS)
	data = r.json()

	if data['status'] != 1:
		quit()

	URLLogin = "http://127.0.0.1:5000/login"
	LOGINPARAMS = {'username': 'cheater', 'password': 'Iheartcheating1'}
	r_login = requests.post(url = URLLogin, data = LOGINPARAMS)
	login_data = r_login.json()

	solution = {"status": 1, "jwt": 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJjaGVhdGVyIiwgImFjY2VzcyI6ICJUcnVlIiwgIm1vZGVyYXRvciI6ICJUcnVlIn0=.768329b0328fb2dbd99a102ce4c657d71452613035e7e6e38a3de56a5afc0cd4'}
	for key in solution:
		print(solution[key])
		print(login_data[key])
		if solution[key] != login_data[key]:
			quit()
	# 'tags': json.dumps({'tag1': '#ifyaaintcheatingyaainttrying', 'tag2': '#cheatercheaterpumpkineater'})
	URLCreatePost = "http://127.0.0.1:5000/create_post"
	CREATEPARAMS = {'title': 'If I Did It: Confessions of the Cheater', 'body': 'I don’t understand what I did wrong except live a life that everyone is jealous of', 'post_id': 37}
	r_post = requests.post(url = URLCreatePost, data = CREATEPARAMS, headers={'Authorization': 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJjaGVhdGVyIiwgImFjY2VzcyI6ICJUcnVlIiwgIm1vZGVyYXRvciI6ICJUcnVlIn0=.768329b0328fb2dbd99a102ce4c657d71452613035e7e6e38a3de56a5afc0cd4'})
	post_data = r_post.json()



	solution = {"status": 1}
	for key in solution:
		if solution[key] != post_data[key]:
			quit()
	


	print('Test Passed')

except:
	print('Test Failed')
