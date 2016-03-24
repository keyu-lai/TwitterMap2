from flask import Flask, request, render_template
import json
import requests
from datetime import datetime

application = Flask(__name__)

@application.route('/')
def index():
    return "hello world!"

@application.route('/sns', methods=['POST'])
def get_global():
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
    	print content['Subject']
    	print content['Message']
    # Comfirm the unsubscription
    elif request.headers['x-amz-sns-message-type'] == 'UnsubscribeConfirmation':
    	print 'UnsubscribeConfirmation'

    return 'notification received'

if __name__=='__main__':
    application.run(host='0.0.0.0', debug=True)