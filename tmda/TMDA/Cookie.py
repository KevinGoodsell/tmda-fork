# -*- python -*-

"""Dated/Sender crypto-cookie functions."""


import string
import time

import Defaults
import HMAC
import Util


def datemac(time):
    """Expects time as a string, and returns an HMAC in hex."""
    datemac = HMAC.new(Defaults.CRYPT_KEY,time).digest()[:3]
    return Util.hexlify(datemac)


def make_dated_cookie(time):
    """Return a dated-style cookie (expire date + HMAC)."""
    expire_time = str(int(time) + Util.seconds(Defaults.TIMEOUT))
    datedmac = datemac(expire_time)
    return expire_time + '.' + datedmac


def make_sender_cookie(address):
    """Return a sender-style cookie based on the given address."""
    sender_cookie = HMAC.new(Defaults.CRYPT_KEY,address).digest()[:3]
    return Util.hexlify(sender_cookie)


def make_dated_address():
    """Return a full dated-style e-mail address."""
    now = '%d' % time.time()
    dated_cookie = make_dated_cookie(now)
    dated_address = Defaults.USERNAME + '-dated-' + dated_cookie + '@' \
                    + Defaults.HOSTNAME
    return dated_address


def make_sender_address(address):
    """Return a full sender-style e-mail address."""
    address = string.lower(address)
    sender_cookie = make_sender_cookie(address)
    sender_address = Defaults.USERNAME + '-sender-' + sender_cookie + \
                    '@' + Defaults.HOSTNAME
    return sender_address

