# -*- python -*-

"""Whitelist functionality."""


import fileinput
import os
import re
import string
import sys

import Defaults


def match(message_headers):
    """Determine whether the Envelope-Sender, From:, or Reply-To:
    matches the WHITELIST."""
    # Extract the e-mail address from Envelope-Sender, From:, and Reply-To:
    Envelope = os.environ.get('SENDER')
    From = message_headers.getaddr('from')[1]
    ReplyTo = message_headers.getaddr('reply-to')[1]

    try:
        regex = None
        whitelist = []
        for line in fileinput.input(Defaults.WHITELIST):
            line = string.strip(line)
            # Comment or blank line?
            if line == '' or line[0] in '#':
                continue
            else:
                whitelist.append(re.escape(line))
        whitelist.sort()
        
        # "address1|address2|address3|addressN"
        regex = string.join(whitelist,'|')
        if regex:
            reo = re.compile(regex, re.I)
        else:
            return 0
        
        for address in (Envelope, From, ReplyTo):
            if address and reo.search(address):
                return 1
  
    except IOError, error_msg:
        print error_msg
        sys.exit(Defaults.ERR_IO)
        
