# -*- python -*-

"""Crypto-cookie functions."""


import os
import string
import time

import Defaults
import HMAC
import Util


def confirmationmac(time,pid,keyword=None):
    """Expects time, pid and optionally keyword as strings,
    and returns an HMAC in hex."""
    chmac = HMAC.hmac(Defaults.CRYPT_KEY)
    chmac.update(time)
    chmac.update(pid)
    if keyword:
        chmac.update(keyword)
    return Util.hexlify(chmac.digest()[:Defaults.HMAC_BYTES])


def make_confirm_cookie(time,pid,keyword=None):
    """Return a confirmation-cookie (timestamp.process_id.HMAC)."""
    timestamp = str(time)
    process_id = str(pid)
    chmac = confirmationmac(timestamp,process_id,keyword)
    return timestamp + '.' + process_id + '.' + chmac


def make_confirm_address(address,time,pid,keyword):
    """Return a full confirmation-style e-mail address."""
    confirm_cookie = make_confirm_cookie(time,pid,keyword)
    (username, hostname) = string.split(address,'@')
    confirm_address = username + Defaults.RECIPIENT_DELIMITER + 'confirm' \
                      + Defaults.RECIPIENT_DELIMITER + keyword + '.' \
                      + confirm_cookie + '@' + hostname
    return confirm_address


def datemac(time):
    """Expects time as a string, and returns an HMAC in hex."""
    datemac = HMAC.new(Defaults.CRYPT_KEY,time).digest()[:Defaults.HMAC_BYTES]
    return Util.hexlify(datemac)


def make_dated_cookie(time):
    """Return a dated-style cookie (expire date + HMAC)."""
    tmda_timeout = os.environ.get('TMDA_TIMEOUT')
    if not tmda_timeout:tmda_timeout = Defaults.TIMEOUT
    expire_time = str(int(time) + Util.seconds(tmda_timeout))
    datedmac = datemac(expire_time)
    return expire_time + '.' + datedmac


def make_dated_address(address):
    """Return a full dated-style e-mail address."""
    now = '%d' % time.time()
    dated_cookie = make_dated_cookie(now)
    (username, hostname) = string.split(address,'@')
    dated_address = username + Defaults.RECIPIENT_DELIMITER + 'dated' + \
                    Defaults.RECIPIENT_DELIMITER + dated_cookie + '@' + hostname
    return dated_address


def make_sender_cookie(address):
    """Return a sender-style cookie based on the given address."""
    sender_cookie = HMAC.new(Defaults.CRYPT_KEY,
                             address).digest()[:Defaults.HMAC_BYTES]
    return Util.hexlify(sender_cookie)


def make_sender_address(address, sender):
    """Return a full sender-style e-mail address."""
    sender = string.lower(sender)
    sender_cookie = make_sender_cookie(sender)
    (username, hostname) = string.split(address,'@')
    sender_address = username + Defaults.RECIPIENT_DELIMITER + 'sender' + \
                     Defaults.RECIPIENT_DELIMITER + sender_cookie + '@' + hostname
    return sender_address
