# -*- python -*-

"""General purpose utility functions."""


import fileinput
import os
import re
import string
import sys


def gethostname():
    hostname = os.environ.get('QMAILHOST') or \
               os.environ.get('MAILHOST')
    if not hostname:
        import socket
        hostname = socket.getfqdn()
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
    """Process and add then each line of a textfile to a list."""
    for address in fileinput.input(file):
        address = string.strip(address)
        # Comment or blank line?
        if address == '' or address[0] in '#':
            continue
        else:
            address = string.lower(address)
            list.append(address)
    return list
