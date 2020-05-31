from flask import Flask, request
import requests
import sys
import os
import json
from Credentials import *
from pymessenger import Bot


app = Flask(__name__)

bot = Bot(PAGE_ACCESS_TOKEN)

@app.route('/', methods=['GET'])
def root():
    return "salut la gang", 200

@app.route('/webhook', methods=['GET'])
# Webhook verification
def handle_verification():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if request.args.get('hub.verify_token', '') != VERIFY_TOKEN:
            return "Error, wrong validation token", 403
        return request.args['hub.challenge'], 200
    return "Webhook successful", 200


@app.route('/', methods=['POST'])
def receive_message():
    data = request.get_json()
    log(data)

    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:

                # IDs
                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']

                if messaging_event.get('message'):
                    # Extracting text message
                    if 'text' in messaging_event['message']:
                        messaging_text = messaging_event['message']['text']
                    else:
                        messaging_text = 'no text'

                    response = None

                    entity, value = wit_response(messaging_text)
                    if entity == 'newstype':
                        response = "Ok, I will send you the {} news".format(str(value))
                    elif entity == 'location':
                        response = "Ok, so you live in {0}. Here are top headlines from {0}".format(str(value))

                    if response == None:
                        response = "I have no idea what you are saying!"
                        
                    bot.send_text_message(sender_id, response)
    return "ok", 200


def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
    log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(port=80)
