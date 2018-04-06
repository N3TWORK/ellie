#!/usr/bin/env python

from flask import Flask, render_template, redirect, request
from twilio.util import TwilioCapability
from twilio.rest import TwilioRestClient
import twilio.twiml
from slackclient import SlackClient
import uuid
import os
import threading

base_url = os.environ["BASE_URL"]

door_unlock_digits = str(os.environ["DOOR_UNLOCK_DIGITS"])

# Slack Integration.
slack_token = os.environ["SLACK_TOKEN"]
slack_channel = os.environ["SLACK_CHANNEL"]
 
# Twilio Integration.
# Find these values at https://twilio.com/user/account
twilio_account_sid = os.environ["TWILIO_ACCOUNT_SID"]
twilio_auth_token = os.environ["TWILIO_AUTH_TOKEN"]
# https://www.twilio.com/user/account/voice/dev-tools/twiml-apps
twilio_application_sid = os.environ["TWILIO_APPLICATION_SID"]

if "TWILIO_MAX_HOLD_DURATION" in os.environ:
    twilio_max_hold_duration = int(os.environ["TWILIO_MAX_HOLD_DURATION"])
else:
    twilio_max_hold_duration = 15 # Seconds
if "TWILIO_FALLBACK_NUMBER" in os.environ:
    twilio_fallback_number = os.environ["TWILIO_FALLBACK_NUMBER"]
else:
    twilio_fallback_number = None

twilio_queue_name = "Ellie Queue"
twilio_client_name = "ellie"

pending_call_sid = None
pending_call_token = None

application = Flask(__name__)


def send_to_fallback():
    if pending_call_token:
        client = TwilioRestClient(twilio_account_sid, twilio_auth_token) 
        if twilio_fallback_number:
            print "sending call to fallback number."
            call = client.calls.update(pending_call_sid, url="{}/fallback?token={}".format(base_url, pending_call_token), method="GET")
        else:
            print "No fallback number. Hanging up."
            client.calls.update(pending_call_sid, status="completed")
        
def wait_for_fallback(call_sid):
    global pending_call_sid
    pending_call_sid = call_sid
    t = threading.Timer(twilio_max_hold_duration, send_to_fallback)
    t.start()

# Post message to slack.
def post_slack_message(msg):
    sc = SlackClient(slack_token)
    sc.api_call("chat.postMessage", channel=slack_channel, text=msg, username='front-desk', icon_emoji=":phone:")


# Endpoint called by Twilio after call is redirected to fallback number.
@application.route('/fallback', methods=['GET', 'POST'])
def fallback():
    global pending_call_token
    global pending_call_sid
    token = request.args.get("token")
    print "/fallback"
    print "pending_call_token: {}".format(pending_call_token)
    print "token: {}".format(token)
    if pending_call_token and (token == pending_call_token):
        post_slack_message("Forwarded call to fallback number")
        pending_call_token = None
        pending_call_sid = None
        return "<Response><Dial>{}</Dial></Response>".format(twilio_fallback_number)
 
    return render_template("answered.html")

# Answer link from slack. Will answer a call if one is outstanding or say the call has already been answered.
@application.route('/answer', methods=['GET', 'POST'])
def answer():
    global pending_call_token
    token = request.args.get("token")
    print "/answer"
    print "pending_call_token: {}".format(pending_call_token)
    print "token: {}".format(token)
    if pending_call_token and (token == pending_call_token):
        return redirect("{}/?token={}".format(base_url, token), code=302)
 
    return render_template("answered.html")


# Twilio voice webhook.
# Either place the call into the queue, or if answer is specified, connect caller with current call in queue.
@application.route('/voice', methods=['GET', 'POST'])
def queue():
    global pending_call_token
    global pending_call_sid
    token = request.args.get("token")

    print "/voice"
    print "pending_call_token: {}".format(pending_call_token)
    print "token: {}".format(token)

    if pending_call_token and (token == pending_call_token):
        r = twilio.twiml.Response()
        with r.dial() as d:
            d.queue(twilio_queue_name)
            pending_call_token = None
            pending_call_sid = None

            post_slack_message("Someone answered the call.")
            return str(r)

    else:
        pending_call_token = str(uuid.uuid4())
        post_slack_message("Someone is calling. <{}/answer?token={}|Click to answer>".format(base_url, pending_call_token))
        r = twilio.twiml.Response()
        r.enqueue(twilio_queue_name)
        call_sid = request.args.get("CallSid")
        wait_for_fallback(call_sid)
 
        return str(r)

# The web client interface. 
@application.route('/', methods=['GET', 'POST'])
def client():
    global pending_call_token
    token = request.args.get("token")

    print "/"
    print "pending_call_token: {}".format(pending_call_token)
    print "token: {}".format(token)
    
    if pending_call_token and (token == pending_call_token):
        capability = TwilioCapability(twilio_account_sid, twilio_auth_token)
        capability.allow_client_outgoing(twilio_application_sid)
        capability.allow_client_incoming(twilio_client_name)
        twilio_token = capability.generate()
 
        return render_template('client.html', twilio_token=twilio_token, call_token=pending_call_token, door_unlock_digits=door_unlock_digits)
    else:
        return render_template("answered.html")
 
if __name__ == "__main__":
    application.debug = True
    application.run()
