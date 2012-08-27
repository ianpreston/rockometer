from flask import Flask, request, render_template, g
from flask.ext.basicauth import BasicAuth
from storm.locals import create_database, Store, Desc, Int, Unicode, Bool, DateTime
import os
import os.path
import datetime

app = Flask(__name__)
app.config.from_object('config')

basic_auth = BasicAuth(app)

class Vote(object):
    __storm_table__ = 'votes'
    id = Int(primary=True)
    direction = Int()
    fromNumber = Unicode()
    active = Bool()
    created_at = DateTime()

    def __init__(self, direction, fromNumber):
        self.direction = direction
        self.fromNumber = fromNumber
        self.active = True
        self.created_at = datetime.datetime.now()


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

def sms(message):
    return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>{0}</Sms></Response>'.format(message)


##
# SMS Commands
##

def cmd_reset():
    g.store.find(Vote).set(active=False)
    set_settings(active=True)
    g.store.commit()

    return sms('Great, the meter has been reset.')


def cmd_stop():
    set_settings(active=False)
    g.store.commit()
    return sms('Voting is now inactive.')


def cmd_start():
    set_settings(active=True)
    g.store.commit()
    return sms('Voting is now active.')


def vote(direction):
    if get_settings().active == False:
        return sms('Sorry, voting has already ended for this round.')

    if app.config['MAX_VOTES'] != -1 and \
       g.store.find(Vote, fromNumber=request.form['From'], active=True).count() >= app.config['MAX_VOTES']:
        return sms('Sorry, you\'ve already voted for this round.')

    vote = Vote(direction, request.form['From'])
    g.store.add(vote)
    g.store.flush()
    g.store.commit()

    if g.store.find(Vote, fromNumber=request.form['From'], active=True).count() == 1:
        return sms('Great, your vote has been recorded.')
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
    # initialize it
    script_dir = os.path.dirname(__file__)
    database_abs = os.path.join(script_dir, app.config['DATABASE_FILENAME'])
    dbinit_abs = os.path.join(script_dir, 'dbinit.sql')
    if os.path.exists(database_abs) == False:
        os.system('sqlite3 ' + database_abs + ' < ' + dbinit_abs)

    g.db = create_database('sqlite:///' + database_abs)
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


@app.route('/admin/')
@basic_auth.required
def admin_index():
    return render_template('admin/index.html',
                           votes=g.store.find(Vote).order_by(Desc(Vote.id)))

@app.route('/admin/_actions/stop')
@basic_auth.required
def admin_actions_stop():
    set_settings(active=False)
    g.store.commit()
    return 'success'

@app.route('/admin/_actions/start')
@basic_auth.required
def admin_actions_start():
    set_settings(active=True)
    g.store.commit()
    return 'success'

@app.route('/admin/_actions/reset')
@basic_auth.required
def admin_actions_reset():
    g.store.find(Vote).set(active=False)
    set_settings(active=True)
    g.store.commit()
    return 'success'

@app.route('/_twilio/sms', methods=['POST'])
def twilio_sms():
    if app.config['TESTING'] != True:
        if request.form['AccountSid'] != app.config['TWILIO_ACCOUNT_SID']:
            return 'You\'re not twilio!'

    command = request.form['Body'].upper().strip("\n ")

    if command in ADMIN_COMMANDS:
        if request.form['From'] not in app.config['ADMIN_PHONE_NUMBERS']:
            return sms('Sorry, you\'re not an adminstrator.')

        return (ADMIN_COMMANDS[command])()

    elif command in USER_COMMANDS:
        return (USER_COMMANDS[command])()

    else:
        return sms('Please text either SUCK or ROCK.')


##
# Template filters
##

@app.template_filter('prettifydid')
def prettify_did(did):
    # Strip country code (assuming 1-digit country code) and add dashes
    return did[2:5] + '-' + did[5:8] + '-' + did[8:]
    
if __name__ == '__main__':
    app.run()