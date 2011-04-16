# -*- python -*-
#
# Copyright (C) 2001-2007 Jason R. Mastaler <jason@mastaler.com>
#
# This file is part of TMDA.
#
# TMDA is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  A copy of this license should
# be included in the file COPYING.
#
# TMDA is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with TMDA; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""Crypto-cookie functions."""


import base64
import os
import re
import time
import hmac
from hashlib import sha1

import Defaults
import Util

def tmda_mac(*items):
    """Create a SHA-1 HMAC based on items (which must be strings)
    and return a hex string cropped to HMAC_BYTES."""
    mac = hmac.new(Defaults.CRYPT_KEY, ''.join(items), sha1)
    hex_size = 2 * Defaults.HMAC_BYTES
    return mac.hexdigest()[:hex_size]


def confirmationmac(time, pid, keyword=None):
    """Expects time, pid and optionally keyword as strings,
    and returns an HMAC in hex."""
    if keyword is None:
        keyword = ''
    return tmda_mac(time, pid, keyword)


def make_confirm_cookie(time, pid, keyword=None):
    """Return a confirmation-cookie (timestamp.process_id.HMAC)."""
    timestamp = str(time)
    process_id = str(pid)
    chmac = confirmationmac(timestamp, process_id, keyword)
    return '%s.%s.%s' % (timestamp, process_id, chmac)


def make_confirm_address(address, time, pid, keyword=None):
    """Return a full confirmation-style e-mail address."""
    confirm_cookie = make_confirm_cookie(time, pid, keyword)
    if Defaults.CONFIRM_ADDRESS:
        address = Defaults.CONFIRM_ADDRESS
    username, hostname = address.split('@')
    confirm_address = '%s%s%s%s%s@%s' % (username,
                                         Defaults.RECIPIENT_DELIMITER,
                                         Defaults.TAGS_CONFIRM[0],
                                         Defaults.RECIPIENT_DELIMITER,
                                         confirm_cookie, hostname)
    return confirm_address


def datemac(time):
    """Expects time as a string, and returns an HMAC in hex."""
    return tmda_mac(time)


def make_dated_cookie(time, timeout = None):
    """Return a dated-style cookie (expire date + HMAC)."""
    tmda_timeout = timeout or os.environ.get('TMDA_TIMEOUT')
    if not tmda_timeout:tmda_timeout = Defaults.DATED_TIMEOUT
    expire_time = str(int(time) + Util.seconds(tmda_timeout))
    datedmac = datemac(expire_time)
    return expire_time + '.' + datedmac


def make_dated_address(address, addrtime=None):
    """Return a full dated-style e-mail address."""
    if addrtime is None:
        addrtime = time.time()
    dated_cookie = make_dated_cookie(addrtime)
    username, hostname = address.split('@')
    dated_address = '%s%s%s%s%s@%s' %(username,
                                      Defaults.RECIPIENT_DELIMITER,
                                      Defaults.TAGS_DATED[0],
                                      Defaults.RECIPIENT_DELIMITER,
                                      dated_cookie, hostname)
    return dated_address


def make_sender_cookie(address):
    """Return a sender-style cookie based on the given address."""
    return tmda_mac(address.lower())


def make_sender_address(address, sender):
    """Return a full sender-style e-mail address."""
    sender_cookie = make_sender_cookie(sender)
    username, hostname = address.split('@')
    sender_address = '%s%s%s%s%s@%s' %(username,
                                       Defaults.RECIPIENT_DELIMITER,
                                       Defaults.TAGS_SENDER[0],
                                       Defaults.RECIPIENT_DELIMITER,
                                       sender_cookie, hostname)
    return sender_address


def make_keywordmac(keyword):
    """Expects a keyword as a string, returns an HMAC in hex."""
    return tmda_mac(keyword)


def make_keyword_cookie(keyword):
    """Return a keyword-style cookie (keyword + HMAC)."""
    # Characters outside of an RFC2822 atom token are changed to '?'
    keyword = re.sub("[^-a-zA-Z0-9!#$%&*+/=?^_`{|}'~]", "?", keyword)
    # We don't allow the RECIPIENT_DELIMITER in a keyword; replace with `?'
    keyword = keyword.replace(Defaults.RECIPIENT_DELIMITER, '?')
    keywordmac = make_keywordmac(keyword)
    return '%s.%s' % (keyword, keywordmac)


def make_keyword_address(address, keyword):
    """Return a full keyword-style e-mail address."""
    keyword = keyword.lower()
    keyword_cookie = make_keyword_cookie(keyword)
    username, hostname = address.split('@')
    keyword_address = '%s%s%s%s%s@%s' %(username,
                                        Defaults.RECIPIENT_DELIMITER,
                                        Defaults.TAGS_KEYWORD[0],
                                        Defaults.RECIPIENT_DELIMITER,
                                        keyword_cookie, hostname)
    return keyword_address


def make_fingerprint(hdrlist):
    """Expects a list of strings, and returns a full (unsliced) HMAC
    as a base64 encoded string, but with the trailing '=' and newline
    removed."""
    fp = hmac.new(Defaults.CRYPT_KEY, digestmod=sha1)
    for hdr in hdrlist:
        fp.update(hdr)
    return base64.encodestring(fp.digest())[:-2] # Remove '=\n'
