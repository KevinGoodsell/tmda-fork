# -*- python -*-

"""General purpose functions."""


import fileinput
import os
import re
import string
import sys
import types


def hexlify(b):
    """Return the hexadecimal representation of the binary data."""
    return "%02x"*len(b) % tuple(map(ord, b))


def unhexlify(s):
    """Return the binary data represented by the hexadecimal string."""
    acc = []
    append = acc.append
    int16 = string.atoi
    for i in range(0, len(s), 2):
        append(chr(int16(s[i:i+2], 16)))
    return string.join(acc, '')


def gethostname():
    hostname = os.environ.get('QMAILHOST') or \
               os.environ.get('MAILHOST')
    if not hostname:
        import socket
        hostname = socket.gethostbyaddr(socket.gethostname())[0]
    return hostname


def getfullname():
    fullname = os.environ.get('QMAILNAME') or \
               os.environ.get('NAME') or \
               os.environ.get('MAILNAME')
    if not fullname:
        import pwd
        fullname = pwd.getpwuid(os.getuid())[4]
    if not fullname:
        fullname = ''
    return fullname


def getusername():
    username = os.environ.get('QMAILUSER') or \
               os.environ.get('USER') or \
               os.environ.get('LOGNAME')
    if not username:
        import pwd
        username = pwd.getpwuid(os.getuid())[0]
    if not username:
        username = '<unknown>'
    return username


def seconds(timeout):
    """Translate the defined timeout interval into seconds."""
    if re.match("^[0-9]+w",timeout):   # weeks --> seconds
        seconds = int(string.replace(timeout,"w","")) * 60 * 60 * 24 * 7
    elif re.match("^[0-9]+d",timeout): # days --> seconds
        seconds = int(string.replace(timeout,"d","")) * 60 * 60 * 24
    elif re.match("^[0-9]+h",timeout): # hours --> seconds
        seconds = int(string.replace(timeout,"h","")) * 60 * 60
    elif re.match("^[0-9]+m",timeout): # minutes --> seconds
        seconds = int(string.replace(timeout,"m","")) * 60
    elif re.match("^[0-9]+s",timeout): # just seconds
        seconds = int(string.replace(timeout,"s",""))
    else:
        print "Invalid timeout value:", timeout
        sys.exit(ERR_CONFIG)
    return seconds


def format_timeout(timeout):
    """Return a human readable translation of the timeout interval."""
    if re.match("^[0-9]+w",timeout):
        timeout = string.replace(timeout,"w"," weeks")
    elif re.match("^[0-9]+d",timeout):
        timeout = string.replace(timeout,"d"," days")
    elif re.match("^[0-9]+h",timeout):
        timeout = string.replace(timeout,"h"," hours")
    elif re.match("^[0-9]+m",timeout):
        timeout = string.replace(timeout,"m"," minutes")
    elif re.match("^[0-9]+s",timeout):
        timeout = string.replace(timeout,"s"," seconds")
    else:
        pass
    return timeout


def file_to_dict(file,dict):
    """Process and add then each line of a textfile to a dictionary."""
    for line in fileinput.input(file):
        line = string.strip(line)
        # Comment or blank line?
        if line == '' or line[0] in '#':
            continue
        else:
            fields = string.split(line)
            key = fields[0]
            key = string.lower(key)
            value = fields[1]
            dict[key] = value
    return dict


def file_to_list(file,list):
    """Process and then append each line of file to list."""
    for line in fileinput.input(file):
        line = string.strip(line)
        # Comment or blank line?
        if line == '' or line[0] in '#':
            continue
        else:
            line = string.expandtabs(line)
            line = string.split(line, ' #')[0]
            line = string.strip(line)
            line = string.lower(line)
            list.append(line)
    return list


def findmatch(list,address):
    """Determine whether the substring address is contained in list.
    Return the 2nd half of the string if it exists (for exp and ext
    addresses only)."""
    for s in list:
        stringparts = string.split(s)
        if string.find(address,stringparts[0]) != -1:
            try:
                return stringparts[1]
            except IndexError:
                return 1


def substring_match(substrings, *addrs):
    """Determine whether any of the passed e-mail addresses match a
    substring contained in substrings which might be a list or a file."""
    try:
        regex = None
        sublist = []

        if type(substrings) is types.ListType:
            for sub in substrings:
                sublist.append(re.escape(sub))
        # We assume a file if substrings is not a list.
        else:                          
            for line in fileinput.input(substrings):
                line = string.strip(line)
                # Comment or blank line?
                if line == '' or line[0] in '#':
                    continue
                else:
                    line = string.expandtabs(line)
                    line = string.split(line, ' #')[0]
                    line = string.strip(line)
                    sublist.append(re.escape(line))
        
        # "address1|address2|address3|addressN"
        regex = string.join(sublist,'|')
        if regex:
            reo = re.compile(regex, re.I)
        else:
            return 0
        
        for address in addrs:
            if address and reo.search(address):
                return 1
  
    except IOError, error_msg:
        import Defaults
        print error_msg
        sys.exit(Defaults.ERR_IO)


def maketext(templatefile, vardict):
    """Make some text from a template file.
    Adapted from Mailman's Util.maketext().

    Reads the `templatefile', from ../templates/, does string
    substitution by interpolating in the `localdict'.
    """
    # ../templates/
    template_dir = os.path.split(os.path.dirname
                                 (os.path.abspath
                                  (sys.argv[0])))[0] + '/templates'
    file = os.path.join(template_dir, templatefile)
    fp = open(file)
    template = fp.read()
    fp.close()
    import Defaults
    localdict = Defaults.__dict__.copy()
    localdict.update(vardict)
    text = template % localdict
    return text
