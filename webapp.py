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

        # Are votes still accepted, or has voting ended?
        self.is_active = True


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


def cmd_reset():
    g.db.data.reset()
    g.db.save()
    return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Great, the meter has been reset.</Sms></Response>'


def cmd_stop():
    g.db.data.is_active = False
    g.db.save()

    return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Voting is now inactive.</Sms></Response>'


def vote(direction):
    if not g.db.data.is_active:
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, voting has already ended for this round.</Sms></Response>'

    if (request.form['From'] in g.db.data.voters) and (app.config['MULTIPLE_VOTES_ALLOWED'] == False):
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, you\'ve already voted for this round.</Sms></Response>'

    g.db.data.voters.append(request.form['From'])
    g.db.data.score += direction
    g.db.save()

    return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Great, your vote has been recorded.</Sms></Response>'


ADMIN_COMMANDS = {
    'RESET': cmd_reset,
    'STOP': cmd_stop,
}

USER_COMMANDS = {
    'ROCK': (lambda: vote(1)),
    'SUCK': (lambda: vote(-1)),
}


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


@app.route('/meter/isactive')
def get_is_active():
    return 'y' if g.db.data.is_active else 'n'


@app.route('/_twilio/sms', methods=['POST'])
def twilio_sms():
    if app.config['TESTING'] != True:
        # Verify that it is actually Twilio making the request
        if request.form['AccountSid'] != app.config['TWILIO_ACCOUNT_SID']:
            return 'You\'re not twilio!'

    command = request.form['Body'].upper().strip("\n ")

    if command in ADMIN_COMMANDS:
        if request.form['From'] not in app.config['ADMIN_PHONE_NUMBERS']:
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, you\'re not an adminstrator.</Sms></Response>'

        return (ADMIN_COMMANDS[command])()

    elif command in USER_COMMANDS:
        return (USER_COMMANDS[command])()

    else:
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Please text either SUCK or ROCK.</Sms></Response>'
    
    
if __name__ == '__main__':
    app.run()