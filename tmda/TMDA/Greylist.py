# -*- python -*-

"""Blacklist/Whitelist functionality."""


import fileinput
import os
import re
import string
import sys

import Defaults


def match(message_headers,listfile):
    """Determine whether the Envelope-Sender, From:, or Reply-To:
    matches the listfile."""
    # Extract the e-mail address from Envelope-Sender, From:, and Reply-To:
    Envelope = os.environ.get('SENDER')
    From = message_headers.getaddr('from')[1]
    ReplyTo = message_headers.getaddr('reply-to')[1]

    try:
        regex = None
        greylist = []
        for line in fileinput.input(listfile):
            line = string.strip(line)
            # Comment or blank line?
            if line == '' or line[0] in '#':
                continue
            else:
                greylist.append(re.escape(line))
        greylist.sort()
        
        # "address1|address2|address3|addressN"
        regex = string.join(greylist,'|')
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
        
