# -*- python -*-

"""General purpose functions."""


import fileinput
import fnmatch
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
        try:
            hostname = socket.getfqdn() # Python2 only
        except AttributeError:
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
    match = re.match("^([0-9]+)([YMwdhms])$", timeout)
    if not match:
        print "Invalid timeout value:", timeout
        import Defaults
        sys.exit(Defaults.EX_TEMPFAIL)
    (num, unit) = match.groups()
    if unit == 'Y':                     # years --> seconds
        seconds = int(num) * 60 * 60 * 24 * 365
    elif unit == 'M':                   # months --> seconds
        seconds = int(num) * 60 * 60 * 24 * 30
    elif unit == 'w':                   # weeks --> seconds
        seconds = int(num) * 60 * 60 * 24 * 7
    elif unit == 'd':                   # days --> seconds
        seconds = int(num) * 60 * 60 * 24
    elif unit == 'h':                   # hours --> seconds
        seconds = int(num) * 60 * 60
    elif unit == 'm':                   # minutes --> seconds
        seconds = int(num) * 60
    else:                               # just seconds
        seconds = int(num)
    return seconds


def format_timeout(timeout):
    """Return a human readable translation of the timeout interval."""
    match = re.match("^([0-9]+)([YMwdhms])$", timeout)
    if not match:
        return timeout
    (num, unit) = match.groups()
    if unit == 'Y':
        timeout = num + " years"
    elif unit == 'M':
        timeout = num + " months"
    elif unit == 'w':
        timeout = num + " weeks"
    elif unit == 'd':
        timeout = num + " days"
    elif unit == 'h':
        timeout = num + " hours"
    elif unit == 'm':
        timeout = num + " minutes"
    else:
        timeout = num + " seconds"
    if int(num) == 1:
        timeout = timeout[:-1]
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


def findmatch(list, addrs):
    """Determine whether any of the passed e-mail addresses match a
    Unix shell-style wildcard pattern contained in list.  The
    comparison is case-insensitive.  Also, return the second half of
    the string if it exists (for exp and ext addresses only)."""
    for address in addrs:
        if address:
            address = string.lower(address)
            for p in list:
                stringparts = string.split(p)
                p = stringparts[0]
                # Handle special @=domain.dom syntax.
                try:
                    at = string.rindex(p, '@')
                    atequals = p[at+1] == '='
                except (ValueError, IndexError):
                    atequals = None
                if atequals:
                    p1 = p[:at+1] + p[at+2:]
                    p2 = p[:at+1] + '*.' + p[at+2:]
                    match = (fnmatch.fnmatch(address,p1)
                             or fnmatch.fnmatch(address,p2))
                else:
                    match = fnmatch.fnmatch(address,p)
                if match:
                    try:
                        return stringparts[1]
                    except IndexError:
                        return 1


def substring_match(substrings, *addrs):
    """Determine whether any of the passed e-mail addresses match a
    substring contained in substrings which might be a list or a file.
    Currently unused."""
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
        sys.exit(Defaults.EX_TEMPFAIL)


def maketext(templatefile, vardict):
    """Make some text from a template file.
    Adapted from Mailman's Util.maketext().

    Reads the `templatefile' which should be a full pathname, and does
    string substitution by interpolating in the `localdict'.
    """
    fp = open(templatefile)
    template = fp.read()
    fp.close()
    import Defaults
    try:
        localdict = Defaults.__dict__.copy()
        localdict.update(vardict)
        text = template % localdict
        return text
    except KeyError, error_msg:
        print error_msg,'is not a valid template variable'
        sys.exit(Defaults.EX_TEMPFAIL)


def writefile(contents,fullpathname):
    """Simple function to write contents to a file."""
    if os.path.exists(fullpathname):
        import Defaults
        print fullpathname,"already exists"
        sys.exit(Defaults.EX_TEMPFAIL)
    else:
        try:
            file = open(fullpathname,'w')
            file.write(contents)
            file.close()
        except IOError, error_msg:
            import Defaults
            print error_msg
            sys.exit(Defaults.EX_TEMPFAIL)


def append_to_file(str,fullpathname):
    """Append a string to a text file if it isn't already in there."""
    try:
        if os.path.exists(fullpathname):
            for line in fileinput.input(fullpathname):
                line = string.lower(string.strip(line))
                # Comment or blank line?
                if line == '' or line[0] in '#':
                    continue
                else:
                    if string.lower(string.strip(str)) == line:
                        fileinput.close()
                        return 0
        file = open(fullpathname,'a+')
        file.write(string.strip(str) + '\n')
        file.close()
    except IOError, error_msg:
        import Defaults
        print error_msg
        sys.exit(Defaults.EX_TEMPFAIL)


def filter_match(filename, recip, sender=None):
    """Check if the give e-mail addresses match lines in filename."""
    import FilterParser 
    filter = FilterParser.FilterParser(checking=1)
    filter.read(filename)
    (action,action_option,matchline) = filter.firstmatch(recip, [sender])
    # print the results
    checking_msg = 'Checking ' + filename
    print checking_msg
    print '-' * len(checking_msg)
    if recip:
        print 'To:',recip
    if sender:
        print 'From:',sender
    print '-' * len(checking_msg)
    if action:
        print 'MATCH:', matchline
    else:
        print 'Sorry, no matching lines.'
