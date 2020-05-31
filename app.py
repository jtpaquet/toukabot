from flask import Flask, request
import requests
import sys
import os
import json
from Credentials import *
from pymessenger import Bot
from pymongo import MongoClient
from datetime import datetime



app = Flask(__name__)

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_URI = "mongodb+srv://jtpaquet:pv9E9SB5gAVzKWbW@toukaanalytics-epm7v.gcp.mongodb.net/ToukaAnalytics?retryWrites=true&w=majority"
DBS_NAME = 'ToukaAnalytics'
FIELDS = {'content': True, 'author' : True, 'timestamp' : True, 'type' : True}

bot = Bot(PAGE_ACCESS_TOKEN)

@app.route('/', methods=['GET'])
# Webhook verification
def handle_verification():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if request.args.get('hub.verify_token', '') != VERIFY_TOKEN:
            return "Error, wrong validation token", 403
        return request.args['hub.challenge'], 200
    return "Webhook successful", 200

	
@app.route('/', methods=['POST'])
def handle_messages():
    data = request.get_json()
    log(data)
	
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    message_text = str(messaging_event["message"]["text"])

                    send_message(sender_id, message_text)

                if messaging_event.get("delivery"):
                    pass

                if messaging_event.get("optin"):
                    pass

                if messaging_event.get("postback"):
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    # if "@M. Touka-poom" in message_text:
    msg = ""
    handle_stat_req(message_text)
    if msg == "":
        msg = "Je ne comprends pas, tapez !help pour afficher les commandes."

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": msg
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
    log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print(message)
    sys.stdout.flush()

def handle_stat_req(message):
    # DB connection
    log("Connection to database")
    connection = MongoClient(MONGODB_URI)
    database = connection[DBS_NAME]
    members = database['members']
    messages = database['messages_23avril2020']
    pseudos = {author['name'] : author['pseudo'] for author in list(members.find())}
    connection.close()
    msg = ""

    if "!msg" in message: # Tested
        msg += "Overall messages\n"
        stats = list(messages.aggregate( [ { "$collStats": { "storageStats": { } } } ] ))[0]['storageStats']['count']
        msg += f"{stats}\n\n"

    if "!birth" in message: # Tested
        msg += "Création de Touka\n"
        date_min = list(messages.aggregate([{"$group":{"_id": {}, "date_min": { "$min": "$timestamp" }}}]))[0]['date_min']
        msg += str(datetime.fromtimestamp(date_min/1000)) +"\n\n"

    if "!members" in message: # Tested, rajouter depuis quand ils sont membres
        msg += "Membres\n"
        for m in sorted(pseudos.values()):
            msg += f"{m}\n"
        msg += "\n"

    if "!overall_msg" in message: # Tested
        msg += "Overall messages ranking\n"
        stats = {pseudos[d['_id']] : d['count'] for d in list(messages.aggregate([{"$sortByCount": "$author"}]))}
        for key in stats.keys():
            msg += f"{key} : {str(stats[key])} \n"
        msg += f"Total : {sum(stats.values())}"
        msg += "\n"

    if "!overall_word" in message: # Tested
        msg += "Overall words ranking\n"
        n_word_pipeline = [{"$match": {"content": {"$exists":True}}},{"$project": {"author": 1, "n_word": {"$size": {"$split": ["$content", " "]}}}}, {"$group" : { "_id" : "$author", "n_word" : {"$sum":"$n_word"}}}]
        stats = {pseudos[d['_id']] : d['n_word'] for d in list(messages.aggregate(n_word_pipeline))}
        stats = {k: v for k, v in sorted(stats.items(), key=lambda item: item[1])[::-1]}
        for key in stats.keys():
            msg += f"{key} : {str(stats[key])}\n"
        msg += f"Total : {sum(stats.values())}"
        msg += "\n"

    # if "!msg_month" in message:
    #     msg += ""

    # if "!msg_year" in message:
    #     msg += ""

    if "!reactions_made" in message: # Tested
        "Reactions made\n"
        react_made_by_actor_pipeline = [{"$unwind": "$reactions"}, {"$sortByCount": "$reactions.actor"}]
        stats = list(messages.aggregate(react_made_by_actor_pipeline))
        for elem in stats: 
            msg += f"{elem['_id']} : {elem['count']}\n"
        msg += "\n"

    # if "!reactions_received" in message:
    #     "Reactions received\n"
    #     react_received_by_author_pipeline = [{ "$group": {"_id": "$author", "count": {"$sum":  {"$size": "$reactions"}}} }]
    #     stats = list(messages.aggregate(react_received_by_author_pipeline))
    #     for elem in stats: 
    #         msg += f"{elem['_id']} : {elem['count']}\n"
    #     msg += "\n"
    # return msg

    if "!random" in message:
        "Random message\n"
        pipeline = [{ "$sample": { "size": 1 } }]
        r_msg = list(messages.aggregate(pipeline))[0]
        while 'content' not in r_msg.keys():
            r_msg = list(messages.aggregate(pipeline))[0]
        msg += f"{pseudos[r_msg['author']]} : {r_msg['content']}\n"
        msg += str(datetime.fromtimestamp(r_msg["timestamp"]/1000)) + "\n\n"

    if "!help" in message:
        help(messages)

    log(msg)


def help(messages):
    date_max = list(messages.aggregate([{"$group":{"_id": {}, "date_max": { "$max": "$timestamp" }}}]))[0]['date_max']
    
    msg = "Je suis M. Touka-poom\n"
    msg += f"Statistiques en date du {datetime.fromtimestamp(date_max/1000)}\n"
    msg += "Messages total: !msg\n"
    msg += "Création de Touka: !birth\n"
    msg += "Membres: !members\n"
    msg += "Classement global: !overall_msg\n"
    msg += "Classement global (mots): !overall_word\n"
    # msg += "Classement pour un certain mois: !msg_month mm-aaaa\n"
    # msg += "Classement de messages pour une année: !msg_year aaaa\n"
    msg += "Classement pour les réaction faites: !reactions_made\n"
    # msg += "Classement pour les réaction reçues: !reactions_received\n"
    msg += "Message random: !random\n"
    msg += "Help: !help\n"
    return msg


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
