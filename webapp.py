from flask import Flask, request, render_template, g
from storm.locals import create_database, Store, Int, Unicode, Bool
import os
import os.path

app = Flask(__name__)
app.config.from_object('config')

class Vote(object):
    __storm_table__ = 'votes'
    id = Int(primary=True)
    direction = Int()
    fromNumber = Unicode()
    active = Bool()

    def __init__(self, direction, fromNumber):
        self.direction = direction
        self.fromNumber = fromNumber
        self.active = True


class Settings(object):
    __storm_table__ = 'settings'
    id = Int(primary=True)
    active = Bool()

##
# Helper functions
##

def set_settings(**kwargs):
    g.store.find(Settings).set(**kwargs)


def get_settings():
    return g.store.find(Settings).one()


##
# SMS Commands
##

def cmd_reset():
    g.store.find(Vote).set(active=False)
    set_settings(active=True)
    g.store.commit()

    return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Great, the meter has been reset.</Sms></Response>'


def cmd_stop():
    set_settings(active=False)
    g.store.commit()
    return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Voting is now inactive.</Sms></Response>'


def cmd_start():
    set_settings(active=True)
    g.store.commit()
    return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Voting is now active.</Sms></Response>'


def vote(direction):
    if get_settings().active == False:
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, voting has already ended for this round.</Sms></Response>'

    if app.config['MAX_VOTES'] != -1 and \
       g.store.find(Vote, fromNumber=request.form['From'], active=True).count() >= 1:
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, you\'ve already voted for this round.</Sms></Response>'

    vote = Vote(direction, request.form['From'])
    g.store.add(vote)
    g.store.flush()
    g.store.commit()

    if g.store.find(Vote, fromNumber=request.form['From'], active=True).count() == 1:
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Great, your vote has been recorded.</Sms></Response>'
    else:
        return ''


ADMIN_COMMANDS = {
    'RESET': cmd_reset,
    'STOP': cmd_stop,
    'START': cmd_start,
}

USER_COMMANDS = {
    'ROCK': (lambda: vote(1)),
    'SUCK': (lambda: vote(-1)),
}

##
# Request handlers
##

@app.before_request
def before_request():
    # If the database file does not exist, execute dbinit.sql to
    # initialize it. Assumes that CWD is the same directory as this
    # script
    if os.path.exists(app.config['DATABASE_FILENAME']) == False:
        os.system('sqlite3 ' + app.config['DATABASE_FILENAME'] + ' < ' + 'dbinit.sql')

    g.db = create_database('sqlite:///' + app.config['DATABASE_FILENAME'])
    g.store = Store(g.db)


@app.teardown_request
def teardown_request(exception):
    g.store.close()


@app.route('/')
def index():
    return render_template('index.html',
                           phone_number=app.config['TEXT_NUMBER'],
                           red_to=app.config['RED_TO'],
                           yellow_to=app.config['YELLOW_TO'])


@app.route('/meter/score')
def get_score():
    default_score = 50
    score = default_score + (g.store.find(Vote, Vote.active == True).sum(Vote.direction) or 0)

    return str(score)


@app.route('/meter/isactive')
def get_is_active():
    return 'y' if get_settings().active else 'n'


@app.route('/_twilio/sms', methods=['POST'])
def twilio_sms():
    if app.config['TESTING'] != True:
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