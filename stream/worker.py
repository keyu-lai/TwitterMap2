from streaming_server import q
import boto.sns
import thread
import requests, json, sys

class notification():

	def __init__(self):

		self.conn = boto.sns.connect_to_region(
			'us-east-1',
			aws_access_key_id='AKIAIM24ELNKQQ3RRUFQ',
			aws_secret_access_key='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')
		self.arn = 'arn:aws:sns:us-east-1:386615683938:TwitterMap'

	def publish(self, meg):

		self.conn.publish(self.arn, meg, subject='Tweet')


def get_sentiment(text):

	text = text[:text.rfind('https://')].strip()
	res = None
	try:
		re = requests.post("http://gateway-a.watsonplatform.net/calls/text/TextGetTextSentiment", data={'apikey': '97fc6b55135551d309866e3189fa387feda3de01', 'text': text, 'outputMode': 'json'})
		res = json.loads(re.text)['docSentiment']['type']
	except:
		print json.loads(re.text)
	return res

def worker_thread(tweet, n):

	tweet = json.loads(tweet)
	text = tweet['text']
	sen = get_sentiment(text)
	if sen:
		tweet['sentiment'] = sen
		n.publish(json.dumps(tweet))
		print json.dumps(tweet)

if __name__ == '__main__':

	n = notification()
	while True:
		tweet = q.get_message()
		if tweet:
			thread.start_new_thread(worker_thread, (tweet, n, ))

