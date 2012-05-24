import unittest
import webapp
import tempfile
import os

class RockometerTestCase(unittest.TestCase):
    def setUp(self):
        webapp.app.config['TESTING'] = True
        webapp.app.config['ADMIN_PHONE_NUMBERS'] = ['+15555551234', '+15555554567']
        webapp.app.config['DATABASE_FILENAME'] = tempfile.mkstemp()[1]
        webapp.app.config['MULTIPLE_VOTES_ALLOWED'] = False
        # Remove the tempfile so that the webapp will re-create it with
        # the default values
        os.remove(webapp.app.config['DATABASE_FILENAME'])
        self.app = webapp.app.test_client()
        
        
    def tearDown(self):
        try:
            os.remove(webapp.app.config['DATABASE_FILENAME'])
        except OSError:
            # No big deal. The test just didn't save the file.
            pass
        

    def test_default_score(self):
        assert self.app.get('/meter/score').data == '50'


    def test_voting(self):
        # Impersonate twilio. This seems to make the most sense to me, but it
        # might not be best practice as far as unit testing goes.
        
        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555551',
                                'Body': 'SUCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '49'
        
        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555551',
                                'Body': 'SUCK'})
        assert 'already voted' in r.data
        assert self.app.get('/meter/score').data == '49'
        
        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555552',
                                'Body': 'ROCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '50'
        
        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555553',
                                'Body': 'Neither'})
        assert 'Please text either' in r.data
        assert self.app.get('/meter/score').data == '50'


    def test_multiple_voting(self):
        webapp.app.config['MULTIPLE_VOTES_ALLOWED'] = True

        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555551',
                                'Body': 'SUCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '49'

        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555551',
                                'Body': 'SUCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '48'

        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555551',
                                'Body': 'ROCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '49'


    def test_reset(self):
        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555551',
                                'Body': 'Reset'})
        assert 'not an admin' in r.data
        
        r = self.app.post('/_twilio/sms',
                          data={'From': '15555551234',
                                'Body': 'SUCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '49'
        
        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555551234',
                                'Body': 'Reset'})
        assert 'the meter has been reset' in r.data
        assert self.app.get('/meter/score').data == '50'


    def test_stop(self):
        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555551',
                                'Body': 'ROCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '51'

        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555551234',
                                'Body': 'STOP'})
        assert 'Voting is now inactive' in r.data

        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555552',
                                'Body': 'ROCK'})
        assert 'voting has already ended' in r.data
        assert self.app.get('/meter/score').data == '51'

        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555554567',
                                'Body': 'RESET'})
        assert 'the meter has been reset' in r.data
        assert self.app.get('/meter/score').data == '50'


        r = self.app.post('/_twilio/sms',
                          data={'From': '+15555555552',
                                'Body': 'SUCK'})
        assert 'your vote has been recorded' in r.data
        assert self.app.get('/meter/score').data == '49'



if __name__ == '__main__':
    unittest.main()