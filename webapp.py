from flask import Flask, request, render_template, g
import pickle
import os.path

app = Flask(__name__)
app.config.from_object('config')

class RockometerDB(object):
    """
    An advanced NoSQL database
    """
    def __init__(self):
        # The total score
        self.score = 50

        # The list of phone numbers in E.164 format that have voted
        self.voters = []


@app.before_request
def before_request():
    if os.path.exists(app.config['DATABASE_FILENAME']):
        g.db = pickle.load(open(app.config['DATABASE_FILENAME'], 'r'))
    else:
        g.db = RockometerDB()


def save_db():
    pickle.dump(g.db, open(app.config['DATABASE_FILENAME'], 'w'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/meter/score')
def get_score():
    return str(g.db.score)
    
    
@app.route('/_twilio/sms', methods=['POST'])
def incscore():
    # TODO Verify that it is actually Twilio making the request
    
    if request.form['From'] in g.db.voters:
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Sorry, you\'ve already voted for this round.</Sms></Response>'
    else:
        if 'ROCK' in request.form['Body'].upper():
            g.db.score += 1
        elif 'SUCK' in request.form['Body'].upper():
            g.db.score -= 1
        else:
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Please text either SUCK or ROCK.</Sms></Response>'

        g.db.voters.append(request.form['From'])
        save_db()
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>Great, your vote has been recorded.</Sms></Response>'
    
    
if __name__ == '__main__':
    app.run()