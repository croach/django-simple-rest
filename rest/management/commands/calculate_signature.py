from optparse import make_option
import datetime
import time

from django.core.management.base import BaseCommand
from rest import calculate_signature


class Command(BaseCommand):
    help = """Calculates a signature for the given secret key and set of data.

Prints the timestamp used for the signature calculation and the signature
itself in the format: t=<timestamp> sig=<signature>.

If the --urlencode option is specified the full data, timestamp, and signature
are returned as a URL encoded string."""

    args = "secret_key [key=value key=value ...]"

    option_list = BaseCommand.option_list + (
        make_option('--urlencode', '-e',
            dest='encode',
            action='store_true',
            default=False,
            help='Return the data, timestamp, and signature as URL encoded string.'),
        )

    def handle(self, secret_key, *data, **options):
        # Convert the data from a list of key, value pairs to a dict
        data = dict(item.split('=') for item in data)

        # If the timestamp was specified, use it and remove it from the data
        # before calculating the signature, otherwise, the time use will be
        # now in UTC time.
        timestamp = data.pop('t', None)
        if timestamp:
            timestamp = int(timestamp)
        else:
            dt = datetime.datetime.utcnow()
            timestamp = int(time.mktime(dt.timetuple()))
        signature = calculate_signature(secret_key, data, timestamp)

        # Check if the URL encoding option was specified
        if (options['encode']):
            import urllib
            data['t'] = timestamp
            data['sig'] = signature
            print urllib.urlencode(data)
        else:
            print 't=%d sig=%s' % (timestamp, signature)

