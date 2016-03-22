from streaming_server import q

import requests, json, sys

def get_sentiment(text):

	text = text[:text.rfind('https://')].strip()
	res = None
	try:
		re = requests.post("http://gateway-a.watsonplatform.net/calls/text/TextGetTextSentiment", data={'apikey': 'a52143eb1c30afba87bd891a49862e698ef72d3f', 'text': text, 'outputMode': 'json'})
		res = json.loads(re.text)['docSentiment']['type']
	except:
		print json.loads(re.text)
	return res

if __name__ == '__main__':

	while True:
		tweet = q.get_message()
		if tweet:
			tweet = json.loads(tweet)
			text = tweet['text']
			sen = get_sentiment(text)
			if sen:
				tweet['sentiment'] = sen
				print json.dumps(tweet)

