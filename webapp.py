from flask import Flask, request, render_template, g
import pickle
import os.path

app = Flask(__name__)
app.config.from_object('config')

class RockometerDBData(object):
    def __init__(self):
        self.reset()

    def reset(self):
        # The total score
        self.score = 50

        # The list of phone numbers in E.164 format that have voted
        self.voters = []

class RockometerDB(object):
    """
    A basic flat-file database implementation. The actual data is stored in
    RockometerDB.data, which is an instance of RockometerDBData
    """
    def __init__(self, filename):
        """
        If a database file at `filename' exists, open and use that database
        file. Otherwise, create a new, blank database.
        """
        self.filename = filename
        if os.path.exists(filename):
            self.data = pickle.load(open(self.filename, 'r'))
        else:
            self.data = RockometerDBData()

    def save(self):
        """
        Save the current state of the database to disk.
        """
        pickle.dump(self.data, open(self.filename, 'w'))


@app.before_request
def before_request():
    g.db = RockometerDB(app.config['DATABASE_FILENAME'])


@app.route('/')
def index():
    return render_template('index.html',
                           phone_number=app.config['TEXT_NUMBER'],
                           red_to=app.config['RED_TO'],
                           yellow_to=app.config['YELLOW_TO'])


@app.route('/meter/score')
def get_score():
    return str(g.db.data.score)
    
    
@app.route('/_twilio/sms', methods=['POST'])
def twilio_sms():
    if app.config['TESTING'] != True:
        # Verify that it is actually Twilio making the request
        if request.form['AccountSid'] != app.config['TWILIO_ACCOUNT_SID']:
            return 'You\'re not twilio!'
            
    if 'RESET' in request.form['Body'].upper():
        if request.form['From'] in app.config['ADMIN_PHONE_NUMBERS']:
            g.db.data.reset()
            g.db.save()
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Great, the meter has been reset.</Sms></Response>'
        else:
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, you\'re not an adminstrator.</Sms></Response>'
    
    if request.form['From'] in g.db.data.voters:
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, you\'ve already voted for this round.</Sms></Response>'
    else:
        if 'ROCK' in request.form['Body'].upper():
            g.db.data.score += 1
        elif 'SUCK' in request.form['Body'].upper():
            g.db.data.score -= 1
        else:
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Please text either SUCK or ROCK.</Sms></Response>'

        g.db.data.voters.append(request.form['From'])
        g.db.save()
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Great, your vote has been recorded.</Sms></Response>'
    
    
if __name__ == '__main__':
    app.run()