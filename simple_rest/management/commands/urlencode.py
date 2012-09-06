from optparse import make_option
import calendar, datetime
import urllib

from django.core.management.base import BaseCommand
from ...auth.signature import calculate_signature


class Command(BaseCommand):
    help = """URL encode the given data.

Returns a URL encoded string for the given set of data. If a secret key is
specified, the secure signature is also calculated and added to the result."""

    args = "secret_key [key=value key=value ...]"

    option_list = BaseCommand.option_list + (
        make_option('--secret-key',
            dest='secret-key',
            action='store',
            help='Calculate the secure signature with the secret key'),
        )

    def handle(self, *data, **options):
        # Convert the data from a list of key, value pairs to a dict
        data = dict(item.split('=') for item in data)

        # Get the secret key if one was provided
        secret_key = options.get('secret-key', None)

        if secret_key:
            # If the timestamp was specified, use it and remove it from the data
            # before calculating the signature, otherwise, the time use will be
            # now in UTC time.
            timestamp = data.pop('t', None)
            if timestamp:
                timestamp = int(timestamp)
            else:
                dt = datetime.datetime.utcnow()
                timestamp = calendar.timegm(dt.timetuple())
            signature = calculate_signature(secret_key, data, timestamp)
            data['t'] = timestamp
            data['sig'] = signature

        print urllib.urlencode(data)
