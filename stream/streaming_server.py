from requests_oauthlib import OAuth1
import requests, json
from sqs import queue

# Metadata including authentication info for twitter api and desired keywords.
twitt_auth = OAuth1('p32FdQyWOR7XvikqGrk1WmjD9',
				client_secret='Ywi4Mq4Hae3LvIHlsU9TBO1L1Tn9mjpUMHkfpHoqdzfjmv9gkt',
				resource_owner_key='1646649835-hz23yaCiq16uanq3qghkG9k7SuAO2L3UkqM3IkH',
				resource_owner_secret='pWLADxamvVS5eq3IZ3VjM24ZSqUC3b7UillWMKP76CRyL')

# keywords
kws = set(["music", "python", "sports", "technology", "zombie", "jordan", "gravity", "amazon"])
tables = None

# the sqs object
# make it a global object so that other servers have access to it
q = queue()

def _generate(pattern):
	'''Table generating phase of KMP.
	'''
	table = [0 for i in range(len(pattern))]
	table[0] = -1
	pos, cnd = 2, 0
	while pos < len(pattern):
		if pattern[pos-1] == pattern[cnd]:
			table[pos] = cnd + 1
			cnd += 1; pos += 1
		elif cnd > 0:
			cnd = table[cnd]
		else:
			table[pos] = 0; pos += 1
	return table

def _search(pattern, string):
	'''searching phase of KMP.
	'''
	table = tables[pattern]
	i = 0; j = 0
	while i + j < len(string):
		if pattern[j] == string[i+j]:
			if j == len(pattern)-1: return True
			j += 1
		else:
			if table[j] > -1:
				i = i + j - table[j]; j = table[j]
			else:
				j = 0; i += 1
	return False

def categorize(string, table):
	'''categorize catched tweet to its supposed category(keyword).

	KMP algorithm is used here for reliable and efficient search process.

	Args:
		string: the text field of tweet to be checked.
		table: A set (hash table) of all keywords for lookup.

	Returns:
		The desired pattern or 'NA' shorthanding for 'Not Applicable'.
	'''
	string = string.lower()
	for pattern in table:
		if _search(pattern, string):
			return pattern
	return 'NA'

def jsonify(response, category):
	'''Form json to be stored as document.

	This function checks relevant fields of response json to populate the json
	to be stored. A series of check procedules gurarantees the validness of json.

	Args:
		response: the original tweet json.
		category: the keyword of response.

	Returns:
		Serialized json to be stored.
	'''
	result = {'keyword': category}
	result['coordinates'] = response['coordinates']['coordinates']
	result['text'] = response['text']
	if 'created_at' in response and response['created_at']:
		result['timestamp'] = response['created_at']
	else: 
		result['timestamp'] = None
	if 'user' in response and response['user']:
		result['author'] = response['user']['name']
	else: 
		result['author'] = None
	return json.dumps(result)

if __name__ == '__main__':

	tables = {kw: _generate(kw) for kw in kws}

	res = requests.get('https://stream.twitter.com/1.1/statuses/filter.json',
					stream=True,
					auth=twitt_auth,
					params={'track': ','.join(kws)})

	for tweet in res.iter_lines():
		if tweet:
			tweet = json.loads(tweet)
			if 'coordinates' in tweet and tweet['coordinates'] \
				and 'text' in tweet and tweet['text'] \
				and 'lang' in tweet and tweet['lang'] == 'en':
				category = categorize(tweet['text'], kws)
				if category != 'NA':
					print jsonify(tweet, category)
					q.send_message(jsonify(tweet, category))
