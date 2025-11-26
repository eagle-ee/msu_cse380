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

	PARAMS = {'first_name': 'Tucker', 'last_name': 'IsACheater(In a different sense)', 'username': 'cheater2', 'email_address': 'mel@cheater.com', 'password': 'Iheartcheating1', 'moderator': False, 'salt': 'FE8x1gO+7z0B'}

	r = requests.post(url = URL, data = PARAMS)
	data = r.json()

	URLLogin = "http://127.0.0.1:5000/login"
	LOGINPARAMS = {'username': 'cheater', 'password': 'Iheartcheating1'}
	r_login = requests.post(url = URLLogin, data = LOGINPARAMS)
	login_data = r_login.json()

	solution = {"status": 1, "jwt": 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJjaGVhdGVyIiwgImFjY2VzcyI6ICJUcnVlIiwgIm1vZGVyYXRvciI6ICJUcnVlIn0=.768329b0328fb2dbd99a102ce4c657d71452613035e7e6e38a3de56a5afc0cd4'}

	for key in solution:
		if solution[key] != login_data[key]:
			quit()
	
	URLCreatePost = "http://127.0.0.1:5000/create_post"
	CREATEPARAMS = {'title': 'If I Did It: Confessions of the Cheater', 'body': 'I don’t understand what I did wrong except live a life that everyone is jealous of', 'post_id': 37, 'tags': json.dumps({'tag1': '#ifyaaintcheatingyaainttrying', 'tag2': '#cheatercheaterpumpkineater'})}
	r_post = requests.post(url = URLCreatePost, data = CREATEPARAMS, headers={'Authorization': 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJjaGVhdGVyIiwgImFjY2VzcyI6ICJUcnVlIiwgIm1vZGVyYXRvciI6ICJUcnVlIn0=.768329b0328fb2dbd99a102ce4c657d71452613035e7e6e38a3de56a5afc0cd4'})
	post_data = r_post.json()


	LOGINPARAMS = {'username': 'cheater2', 'password': 'Iheartcheating1'}
	r_login = requests.post(url = URLLogin, data = LOGINPARAMS)

	URLFollow = "http://127.0.0.1:5000/follow"
	FOLLOWPARAMS = {'username': 'cheater'}
	r_follow = requests.post(url = URLFollow, data = FOLLOWPARAMS, headers={'Authorization': 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJjaGVhdGVyMiIsICJhY2Nlc3MiOiAiVHJ1ZSJ9.df06dea4610cb3a49403845e6e8f91e15714d30abb5324d7ba09adca1a63cb0a'})
	follow_data = r_follow.json()

	if follow_data['status'] != 1:
		quit()

	URLLike = "http://127.0.0.1:5000/like"
	LIKEPARAMS = {'post_id': 37}
	r_like = requests.post(url = URLLike, data = LIKEPARAMS, headers={'Authorization': 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJjaGVhdGVyMiIsICJhY2Nlc3MiOiAiVHJ1ZSJ9.df06dea4610cb3a49403845e6e8f91e15714d30abb5324d7ba09adca1a63cb0a'})
	like_data = r_like.json()


	URLSearch = "http://127.0.0.1:5000/search"
	SEARCHPARAMS = {'feed': True}
	r_search = requests.get(url = URLSearch, params = SEARCHPARAMS, headers={'Authorization': 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJjaGVhdGVyMiIsICJhY2Nlc3MiOiAiVHJ1ZSJ9.df06dea4610cb3a49403845e6e8f91e15714d30abb5324d7ba09adca1a63cb0a'})
	search_data = r_search.json()

	expected = json.dumps({'status': 1,'data': {37:{'title': 'If I Did It: Confessions of the Cheater','body': 'I don’t understand what I did wrong except live a life that everyone is jealous of','tags': ['#ifyaaintcheatingyaainttrying', '#cheatercheaterpumpkineater'],'owner': 'cheater','likes': 1}}})
	expected_dict = json.loads(expected)

	for x in expected_dict['data']:
		for y in expected_dict['data'][x]:
			if y == 'tags':
				if len(expected_dict['data'][x][y]) != len(search_data['data'][x][y]):
					quit()
				else:
					for tag in search_data['data'][x][y]:
						if tag not in search_data['data'][x][y]:
							quit()
			elif expected_dict['data'][x][y] != search_data['data'][x][y]:
				quit()


	print('Test Passed')

except:
	print('Test Failed')
