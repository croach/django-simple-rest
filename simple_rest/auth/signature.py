import time
import hmac
import hashlib


def calculate_signature(key, data, timestamp=None):
    """
    Calculates the signature for the given request data.
    """
    # Create a timestamp if one was not given
    if timestamp is None:
        timestamp = int(time.time())

    # Construct the message from the timestamp and the data in the request
    message = str(timestamp) + ''.join("%s%s" % (k,v) for k,v in sorted(data.items()))

    # Calculate the signature (HMAC SHA256) according to RFC 2104
    signature = hmac.HMAC(str(key), message, hashlib.sha256).hexdigest()

    return signature
