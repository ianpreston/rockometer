import unittest
import webapp
import tempfile
import os

class RockometerTestCase(unittest.TestCase):
    def setUp(self):
        webapp.app.config['TESTING'] = True
        webapp.app.config['DATABASE_FILENAME'] = tempfile.mkstemp()[1]
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


if __name__ == '__main__':
    unittest.main()