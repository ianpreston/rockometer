# Rock-O-Meter
The Rock-O-Meter is an SMS-based audience reaction gauge. It is similar to the applause meter in concept, but works via text. Audience members can text the meter either ROCK or SUCK to make it go up or down, respectively.

It is a clone of Gangplank's Sentiment Meter used during Extreme Pitch.

## Installation


## Configuration

Open `config_template.py`, update the options to your satisfaction, and save it as `config.py`.


## Usage

Your users can text either `SUCK` or `ROCK` to the meter's phone number to affect the score.

Your administrators can additionally text the following commands:

 * `RESET` - Remove all votes, reset the meter to 50, and begin voting if it was stopped

 * `STOP` - Prevent any more votes from coming in, but keep the meter's score visible

 * `START` - Start a previously-stopped meter without resetting the score