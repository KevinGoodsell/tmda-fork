# -*- python -*-
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
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

"""General purpose functions."""


import cPickle
import fileinput
import fnmatch
import os
import popen2
import random
import re
import string
import sys
import time


EMPTYSTRING = ''
NL = '\n'
DOT = '.'
from string import whitespace as WHITESPACE


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
    match = re.match("^([0-9]+)([YMwdhms])$", timeout)
    if not match:
        raise ValueError, 'Invalid timeout value: ' + timeout
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


def unixdate(timesecs=None):
    """Return a date string in the format of the UNIX `date' command.  e.g,

    Thu Dec 27 17:54:04 MST 2001

    timesecs is optional, and if not given, the current time is used.
    """
    if not timesecs:
        timesecs = time.time()
    timetuple = time.localtime(timesecs)
    tzname = time.tzname[timetuple[-1]]
    asctime_list = string.split(time.asctime(timetuple))
    asctime_list.insert(len(asctime_list)-1, tzname)
    return string.join(asctime_list)


def make_msgid(timesecs=None, pid=None):
    """Return an rfc2822 compliant Message-ID string, composed of
    date + process id + random integer + 'TMDA' + FQDN  e.g:
    
    <20020204183548.40803.32317.TMDA@nightshade.la.mastaler.com>

    timesecs is optional, and if not given, the current time is used.

    pid is optional, and if not given, the current process id is used.
    """
    if not timesecs:
        timesecs = time.time()
    if not pid:
        import Defaults
        pid = Defaults.PID
    idhost = os.environ.get('QMAILIDHOST')
    if not idhost:
        idhost = gethostname()
    utcdate = time.strftime('%Y%m%d%H%M%S', time.gmtime(timesecs))
    randint = random.randrange(100000)
    message_id = '<%s.%s.%s.TMDA@%s>' % (utcdate, pid, randint, idhost)
    return message_id


def make_date(timesecs=None, localtime=1):
    """Return an RFC 2822 compliant Date: string.
    
    timesecs is optional, and if not given, the current time is used.

    Optional localtime is a flag that when true, returns a date
    relative to the local timezone instead of UTC where possible.

    JRM: Once the email mod is included within TMDA, we can nuke this
    function and use email.Utils.formatdate in all cases.
    """
    if not timesecs:
        timesecs = time.time()
    try:
        from email.Utils import formatdate
        datestr = formatdate(timesecs, localtime)
    except ImportError:
        from rfc822 import formatdate
        datestr = formatdate(timesecs)
    return datestr


def formataddr(pair):
    """The inverse of parseaddr(), this takes a 2-tuple of the form
    (realname, email_address) and returns the string value suitable
    for an RFC 2822 From:, To: or Cc:.
    
    If the first element of pair is false, then the second element is
    returned unmodified.

    JRM: Once the email mod is included within TMDA, we can nuke this
    function and use email.Utils.formataddr.
    """
    specialsre = re.compile(r'[][\()<>@,:;".]')
    escapesre = re.compile(r'[][\()"]')
    name, address = pair
    if name:
        quotes = ''
        if specialsre.search(name):
            quotes = '"'
        name = escapesre.sub(r'\\\g<0>', name)
        return '%s%s%s <%s>' % (quotes, name, quotes, address)
    return address


def file_to_dict(file, dict):
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


def file_to_list(file):
    """Process and then append each line of file to list."""
    list = []
    for line in fileinput.input(file):
        line = string.strip(line)
        # Comment or blank line?
        if line == '' or line[0] in '#':
            continue
        else:
            line = string.expandtabs(line)
            line = string.split(line, ' #')[0]
            line = string.strip(line)
            list.append(line)
    return list


def pipecmd(command, *strings):
    """Run a child process, returning opened pipes for communication.

    command is the program to execute as a sub-process.

    *strings are optional pieces of data to write to command.

    Based on code from getmail
    <URL:http://www.qcc.sk.ca/~charlesc/software/getmail-2.0/>
    Copyright (C) 2001 Charles Cazabon, and licensed under the GNU
    General Public License version 2.
    """
    try:
        popen2._cleanup()
        cmd = popen2.Popen3(command, 1, bufsize=-1)
        cmdout, cmdin, cmderr = cmd.fromchild, cmd.tochild, cmd.childerr
        if strings:
            # Write to the tochild file object.
            for s in strings:
                cmdin.write(s)
            cmdin.flush()
            cmdin.close()
        # Read from the childerr object; command will block until exit.
        err = cmderr.read().strip()
        cmderr.close()
        # Read from the fromchild object.
        out = cmdout.read().strip()
        cmdout.close()
        # Get exit status from the wait() member function.
        r = cmd.wait()
        # If exit status is non-zero, raise an exception with data
        # from childerr.
        if r:
            if os.WIFEXITED(r):
                exitcode = 'exited %i' % os.WEXITSTATUS(r)
                exitsignal = ''
            elif os.WIFSIGNALED(r):
                exitcode = 'abnormal exit'
                exitsignal = 'signal %i' % os.WTERMSIG(r)
            else:
                # Stopped, etc.
                exitcode = 'no exit?'
                exitsignal = ''
            raise IOError, 'command "%s" %s %s (%s)' \
                  % (command, exitcode, exitsignal, err or '')
        elif err:
            # command wrote something to stderr.
            print err
        if out:
            # command wrote something to stdout.
            print out
    except Exception, txt:
        raise IOError, \
              'failure delivering message to command "%s" (%s)' % (command, txt)


def writefile(contents, fullpathname):
    """Simple function to write contents to a file."""
    if os.path.exists(fullpathname):
        raise IOError, fullpathname + ' already exists'
    else:
        file = open(fullpathname, 'w')
        file.write(contents)
        file.close()
        

def append_to_file(str, fullpathname):
    """Append a string to a text file if it isn't already in there."""
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
    file = open(fullpathname, 'a+')
    file.write(string.strip(str) + '\n')
    file.close()


def pager(file):
    """Display file using a UNIX text pager such as less or more."""
    pager_list = []
    pager = os.environ.get('PAGER')
    if pager is None:
        # try to locate less or more if $PAGER is not set
        for prog in ('less', 'more'):
            path = os.popen('which ' + prog).read()
            if path != '':
                pager = path
                break
    for arg in pager.split():
        pager_list.append(arg)
    pager_list.append(file)
    os.spawnvp(os.P_WAIT, pager_list[0], pager_list)


def sendmail(headers, body, recip, return_path=None):
    """Send e-mail by opening a pipe to the sendmail program.

    headers can be either a rfc822.Message instance, or a set of
    rfc822 compatible message headers as a string.

    body is the message body content as a string.

    recip is the recipient e-mail address.

    return_path is an optional e-mail address which the envelope
    sender address of the message will be set to.
    """
    import Defaults
    if return_path is not None:
        env_sender = "-f '%s'" % (return_path)
    else:
        env_sender = ''
    cmd = "%s %s '%s'" % (Defaults.SENDMAIL, env_sender, recip)
    pipecmd(cmd, str(headers), '\n', body)


def build_cdb(filename):
    """Build a cdb file from a text file."""
    import cdb
    try:
        cdbname = filename + '.cdb'
        cdb = cdb.cdbmake(cdbname, cdbname + '.tmp')
        for line in file_to_list(filename):
            linef = line.split()
            key = linef[0].lower()
            try:
                value = linef[1]
            except IndexError:
                value = ''
            cdb.add(key, value)
        cdb.finish()
    except:
        return 0
    else:
        return 1


def build_dbm(filename):
    import anydbm
    import glob
    import tempfile

    try:
        (dbmpath, dbmname) = os.path.split(filename)
        dbmname += '.db'
        tempfile.tempdir = dbmpath
        tmpname = tempfile.mktemp()

        dbm = anydbm.open(tmpname,'n')
        for line in file_to_list(filename):
            linef = line.split()
            key = linef[0].lower()
            try:
                value = linef[1]
            except IndexError:
                value = ''
            dbm[key] = value
        dbm.close()

        for f in glob.glob(tmpname + '*'):
            (tmppath, tmpname) = os.path.split(tmpname)
            newf = f.replace(tmpname,dbmname)
            newf = os.path.join(tmppath, newf)
            os.rename(f, newf)
    except:
        return 0
    else:
        return 1


def pickleit(object, file, bin=0):
    """Store object in a pickle file.
    Optional bin specifies whether to use binary or text pickle format."""
    fp = open(file, 'w')
    cPickle.dump(object, fp, bin)
    fp.close()
    return


def unpickle(file):
    """Retrieve and return object from the file file."""
    fp = open(file, 'r')
    object = cPickle.load(fp)
    fp.close()
    return object


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


def wraptext(text, column=70, honor_leading_ws=1):
    """Wrap and fill the text to the specified column.

    Wrapping is always in effect, although if it is not possible to
    wrap a line (because some word is longer than `column' characters)
    the line is broken at the next available whitespace boundary.
    Paragraphs are also always filled, unless honor_leading_ws is true
    and the line begins with whitespace.

    Includes code from Mailman
    <URL:http://www.gnu.org/software/mailman/mailman.html>
    Copyright (C) 1998,1999,2000,2001 by the Free Software Foundation, Inc.,
    and licensed under the GNU General Public License version 2.
    """
    wrapped = ''
    # first split the text into paragraphs, defined as a blank line
    paras = re.split('\n\n', text)
    for para in paras:
        # fill
        lines = []
        fillprev = 0
        for line in para.split(NL):
            if not line:
                lines.append(line)
                continue
            if honor_leading_ws and line[0] in WHITESPACE:
                fillthis = 0
            else:
                fillthis = 1
            if fillprev and fillthis:
                # if the previous line should be filled, then just append a
                # single space, and the rest of the current line
                lines[-1] = lines[-1].rstrip() + ' ' + line
            else:
                # no fill, i.e. retain newline
                lines.append(line)
            fillprev = fillthis
        # wrap each line
        for text in lines:
            while text:
                if len(text) <= column:
                    line = text
                    text = ''
                else:
                    bol = column
                    # find the last whitespace character
                    while bol > 0 and text[bol] not in WHITESPACE:
                        bol = bol - 1
                    # now find the last non-whitespace character
                    eol = bol
                    while eol > 0 and text[eol] in WHITESPACE:
                        eol = eol - 1
                    # watch out for text that's longer than the column width
                    if eol == 0:
                        # break on whitespace after column
                        eol = column
                        while eol < len(text) and \
                              text[eol] not in WHITESPACE:
                            eol = eol + 1
                        bol = eol
                        while bol < len(text) and \
                              text[bol] in WHITESPACE:
                            bol = bol + 1
                        bol = bol - 1
                    line = text[:eol+1] + '\n'
                    # find the next non-whitespace character
                    bol = bol + 1
                    while bol < len(text) and text[bol] in WHITESPACE:
                        bol = bol + 1
                    text = text[bol:]
                wrapped = wrapped + line
            wrapped = wrapped + '\n'
            # end while text
        wrapped = wrapped + '\n'
        # end for text in lines
    # the last two newlines are bogus
    return wrapped[:-2]


def maketext(templatefile, vardict):
    """Make some text from a template file.

     Several locations are scanned for templatefile, in the following order:
     1. The directory specified by tmda-filter's `-t' option.
     2. Defaults.TEMPLATE_DIR
     3. ../templates/
     4. The package/RPM template directory.

    The first match found stops the search.  In this way, you can
    specialize templates at the desired level, or, if you use only the
    default templates, you don't need to change anything.
    
    Once the templatefile is found, string substitution is performed
    by interpolation in `localdict'.

    Based on code from Mailman
    <URL:http://www.gnu.org/software/mailman/mailman.html>
    Copyright (C) 1998,1999,2000,2001 by the Free Software Foundation, Inc.,
    and licensed under the GNU General Public License version 2.
    """
    import Defaults
    # Calculate the locations to scan.
    searchdirs = []
    searchdirs.append(os.environ.get('TMDA_TEMPLATE_DIR'))
    searchdirs.append(Defaults.TEMPLATE_DIR)
    searchdirs.append(Defaults.PARENTDIR + '/templates/')
    searchdirs.append(sys.prefix + '/share/tmda/')
    searchdirs.append('/etc/tmda/')
    # Start scanning.
    foundit = None
    for dir in searchdirs:
        if dir:
            filename = os.path.join(dir, templatefile)
            if os.path.exists(filename):
                foundit = filename
                break
    if foundit is None:
        raise IOError, "Can't find " + templatefile
    else:
        fp = open(foundit, 'r')
        template = fp.read()
        fp.close()
        localdict = Defaults.__dict__.copy()
        localdict.update(vardict)
        text = template % localdict
        return text
        

def filter_match(filename, recip, sender=None):
    """Check if the give e-mail addresses match lines in filename."""
    import FilterParser 
    filter = FilterParser.FilterParser()
    filter.read(filename)
    (actions, matchline) = filter.firstmatch(recip, [sender])
    # print the results
    checking_msg = 'Checking ' + filename
    print checking_msg
    print '-' * len(checking_msg)
    if recip:
        print 'To:',recip
    if sender:
        print 'From:',sender
    print '-' * len(checking_msg)
    if actions:
        print 'MATCH:', matchline
    else:
        print 'Sorry, no matching lines.'
