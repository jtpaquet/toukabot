from flask import Flask, request
import requests
import sys
import os
import json
from Credentials import *

app = Flask(__name__)


@app.route('/', methods=['GET'])
# Webhook verification
def handle_verification():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if request.args.get('hub.verify_token', '') != VERIFY_TOKEN:
            return "Error, wrong validation token", 403
        return request.args['hub.challenge'], 200
    return "salut la gang", 200


@app.route('/', methods=['POST'])
def receive_message():
    data = request.get_json()
    log(data)
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
