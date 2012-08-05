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

# The maximum number of times a user is allowed to vote. If this is
# set to -1, users will be able to vote an unlimited number of times.
MAX_VOTES = 1

# The color ranges. The meter will display a red area from 0 through
# RED_TO votes, then a yellow area from there through YELLOW_TO votes,
# and finally a green area from then on to 100 votes.
RED_TO = 50
YELLOW_TO = 65