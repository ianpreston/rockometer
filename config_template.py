# Keep this False
DEBUG = False

# The number listed in the instructions. This should be the number you
# registered your app with on Twilio. Any format is acceptable.
TEXT_NUMBER = '(555) 555-5555'

# Where the database file is stored. The default is probably fine.
DATABASE_FILENAME = 'db.sqlite3'

# Your Twilio account SID.
TWILIO_ACCOUNT_SID = ''

# The list of phone numbers that are allowed to text RESET, in E.164 format,
# e.g. (123) 555-1234 would be +11235551234
ADMIN_PHONE_NUMBERS = ['+16025551234']

# Authentication username/password for the admin section of the site
BASIC_AUTH_USERNAME = 'admin'
BASIC_AUTH_PASSWORD = 'admin'

# The maximum number of times a user is allowed to vote. If this is
# set to -1, users will be able to vote an unlimited number of times.
MAX_VOTES = 1