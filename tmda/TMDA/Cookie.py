# -*- python -*-

"""Dated/Sender cookie-related functions."""


from Crypto.Utils import hex2str
from Crypto.Utils import str2hex
import string
import struct
import time

import Defaults
import Util


def make_cipher_object():
    """Return a block ciphering object."""
    Crypto = __import__("Crypto.Cipher.%s" % Defaults.BLOCK_CIPHER)
    cipher = getattr(Crypto.Cipher, Defaults.BLOCK_CIPHER)
    cipherobj = cipher.new(Defaults.CRYPT_KEY, cipher.CBC, Defaults.CRYPT_IV)
    return cipherobj


def make_sender_cookie(address):
    """Return a sender-style cookie in HEX based on the given e-mail address."""
    HashFunc = __import__("Crypto.Hash.%s" % Defaults.HASH_FUNCTION)
    hash = getattr(HashFunc.Hash, Defaults.HASH_FUNCTION)
    hashobj = hash.new()
    hashobj.update(Defaults.CRYPT_IV)
    hashobj.update(Defaults.CRYPT_KEY)
    hashobj.update(address)
    sender_cookie = hashobj.hexdigest()
    return sender_cookie


def make_dated_cookie(time):
    """Return a dated-style cookie in HEX based on the current time."""
    expire_time = time + Util.seconds(Defaults.TIMEOUT)
    expire_time = '%016d' % (expire_time)
    # Pack into an 8-byte binary structure for cipher compatibility.
    packed_expire_time = struct.pack("d",int(expire_time))
    cipherobj = make_cipher_object()
    dated_cookie = str2hex(cipherobj.encrypt(packed_expire_time))
    return dated_cookie


def get_cookie_date(dated_cookie):
    """Decrypt the 16-byte HEX dated-cookie back into a time tuple."""
    cipherobj = make_cipher_object()
    packed_cookiedate = cipherobj.decrypt(hex2str(dated_cookie))
    cookie_date = '%d' % (struct.unpack("d",packed_cookiedate))
    return cookie_date


def make_dated_address():
    """Return a full dated-style e-mail address."""
    now = time.time()
    dated_cookie = make_dated_cookie(now)
    dated_address = Defaults.USERNAME + '-dated-' + dated_cookie + \
                    '@' + Defaults.HOSTNAME
    return dated_address


def make_sender_address(address):
    """Return a full sender-style e-mail address."""
    address = string.lower(address)
    sender_cookie = make_sender_cookie(address)
    sender_address = Defaults.USERNAME + '-sender-' + sender_cookie + \
                    '@' + Defaults.HOSTNAME
    return sender_address

