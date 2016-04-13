from flask import Flask, request, render_template, Response
import json, requests
from stream.elastic_search import temporal_search, proximity_search
from datetime import datetime
import gevent
from gevent.wsgi import WSGIServer

application = Flask(__name__)

host = 'http://40.114.93.37:9200'
ind = 'twitter_again'
mapping_type = 'tweet_sentiment'

COMING_TWEET = 0

def event_stream():
	global COMING_TWEET
	while True:
		if COMING_TWEET > 0:
			while COMING_TWEET > 0:
				COMING_TWEET -= 1
				yield 'data: new megs!\n\n'
		else:
			gevent.sleep(1)

@application.route('/my_event_source')
def sse_request():
	global COMING_TWEET
	COMING_TWEET = 0
	return Response(
			event_stream(),
			mimetype='text/event-stream')

def _init_index():
	url = '/'.join([host, ind])
	is_exist = requests.head(url)
	if is_exist.status_code != 200:
		with open('stream/type_config.json') as f:
			mapping = json.dumps(json.load(f))
		requests.put('/'.join([host, ind]), data=mapping)

def _insert(string):
	url = '/'.join([host, ind, mapping_type])
	res = requests.post(url, data=string)
	while res.status_code != 201 or not res.json()['created']:
		res = requests.post(url, data=string)

def convert(original_time):
	timestamp = datetime.strptime(original_time, '%m-%d-%Y %I:%M %p')
	return timestamp.strftime('%a %b %d %H:%M:%S +0000 %Y')

@application.route('/')
def index():
	return render_template('index.html')

@application.route('/global', methods=['POST'])
def get_global():
	'''View function for sending tweet points

	Args:
		None

	Returns:
		Dumped json file containing desired twitter points.
	'''
	keyword = request.args['kw']
	start = convert(request.args['start'])
	end = convert(request.args['end'])
	search_res = temporal_search(keyword, start, end)
	response = {'tweets': [], 'count': 0, 'pattern': 'global'}
	for item in search_res['hits']['hits']:
		text = "@" + item['_source']['author'] + ": " + item['_source']['text']
		text = text[:text.rfind('https://')].strip()
		sen = item['_source'].get('sentiment')
		coordinates = item['_source']['coordinates']
		response['tweets'].append({"text": text, "sen": sen, "coordinates": coordinates})
		response['count'] += 1
	return json.dumps(response, indent=2)

@application.route('/sns', methods=['POST'])
def get_sns():
	'''Receieve notifications from sns
	'''
	if 'x-amz-sns-message-type' not in request.headers:
		return 'not a valid sns notification'
	content = json.loads(request.get_data())
	# Comfirm the subscription
	if request.headers['x-amz-sns-message-type'] == 'SubscriptionConfirmation':
		print content['SubscribeURL']
		r = requests.get(content['SubscribeURL'])
		print r.text
	# Get the content of message
	elif request.headers['x-amz-sns-message-type'] == 'Notification':
		global COMING_TWEET
		COMING_TWEET += 1
		_insert(str(content['Message']))
	# Comfirm the unsubscription
	elif request.headers['x-amz-sns-message-type'] == 'UnsubscribeConfirmation':
		print 'UnsubscribeConfirmation'

if __name__=='__main__':
	_init_index()
	http_server = WSGIServer(('0.0.0.0', 5000), application)
	http_server.serve_forever()
