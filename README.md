# Ellie: The Door Butler
Do you have a door callbox that calls a phone to let someone in? Do you share that door with a bunch of people in
your office? Does your office use Slack? Configure and deploy Ellie to notify a Slack channel when someone is at
your door. Ellie will then link you to a page that lets you talk to the person at the callbox and then you can let
them in.

Calls are handled by Twilio and use their WebRTC browser client. Chrome and Firefox currently support WebRTC. Safari does not.

## Requirements

- A Twilio account with a phone number. This is the number your callbox will call.
- A Slack account that will notify people when someone is calling from the callbox.
- A place to host this service, like AWS, where you can provide HTTPS.  

## Configuration

### Deploying to AWS
You can host this anywhere that is publically accessible. Here's how to do it on AWS. Run these commands within the directory
you cloned this repo.

Create a new Elastic Beanstalk application:
```
eb init -p python2.7 Ellie
```

Depending on your defaults you might need to specify the AWS region you want to use. If so, run this:
```
eb init -p python2.7 Ellie --region us-east-1
```

Next create the environment within the application you just created:
```
eb create ellie-prod
```

More detailed instructions are <a href="http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html">available from Amazon</a> if you need them.

You must use HTTPS to use WebRTC in most browsers. This means you'll need to assign a CNAME DNS entry that points to your
Elastic Beanstalk name and then you need to enable HTTPS for your Elastic Beanstalk configuration. This can be done in the 
Elastic Beanstalk Dashboard for your newly created environment in the Network Teir->Load Balancing section. You will also need 
to have previously registerd your SSL certificate for use with AWS. <a href="http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/configuring-https.html">More detailed information is available</a>. 

Finally, you want to make sure your Elastic Beanstalk environment type is set to Single instance. This application currently has no 
data persistence layer, so it won't horizontally scale across multiple servers. But I doubt you're going to have that much load on your callbox. 

Verify it's working by visiting your https:// URL. You should see a page that says "Someone has already answerd the door. Thanks."

### Twilio

- If you do not have one already, create a Twilio account.
- <a href="https://www.twilio.com/user/account/voice/dev-tools/twiml-apps/add">Create a TwiML App</a>.
 - Configure the Voice Request URL to use the DNS entry you configured for your deployment like this: https://ellie.example.com/voice. It should be use HTTP GET.
 - Leave the Messaging Request URL blank.
 - Copy down the Sid. This will be `TWILIO_APPLICATION_SID`.
 - Get your account <a href="https://www.twilio.com/user/account/settings">account tokens</a>.
   - Copy the Live AccountSID. This will be `TWILIO_ACCOUNT_SID`.
   - Copy the Live AuthToken. This will be `TWILIO_AUTH_TOKEN`.
- <a href="https://www.twilio.com/user/account/phone-numbers/search">Buy a phone number</a> that your callbox will call when someone is at the door.
- Click on the phone number you purchased and configure it to use Voice and bind it to the TwiML App you just created.

### Slack
You'll need to create a bot to post to Slack when someone calls from the callbox.
- Go to the <a href="https://slack.com/apps">Slack Apps</a> page.
- Click on Configure.
- Click on Custom Integrations.
- Click on Bots.
- Click on Add Configuration.
  - Pick a bot name.
  - Copy down the API Token. This will be `SLACK_TOKEN`.
  
### Update Your Deployment
Now, add Environment Properties from the Software Configuration section of your application configuration in Elastic Beanstalk for the values you copied above. You also must set:
- `BASE_URL` to contain the https:// based URL that points to your deployment. No trailing slash.
- `DOOR_UNLOCK_DIGITS` to contain the digit or digits you key in on a phone to unlock the door when called from the callbox.
- `SLACK_CHANNEL` to contain the #channel name for where the slack notifications should be sent for callbox activity. 


### Test It Out!
Have someone call your phone number from a phone. It should be answered and they will be placed on hold.
At the same time, you should see a Slack notification that someone is at your door. Click on the link in the noticication and
your browser will open. Since this is the first time, your browser will likely ask for permission to use the microphone. Once granted,
the call should be picked up immediately and you can now talk to the caller. Press the "Open Door" button to open the door, or press "Hang Up"
to hang up without opening the door. 

### Configure Your Callbox
Update your callbox to call your newly created phone number.

Enjoy!