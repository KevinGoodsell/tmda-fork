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

"""General purpose functions."""


from cStringIO import StringIO
import cPickle
import email
import email.utils
import fileinput
import fnmatch
import os
import popen2
import re
import socket
import stat
import sys
import tempfile
import textwrap
import time

import Errors


MODE_EXEC = 01
MODE_READ = 04
MODE_WRITE = 02
POSIX_NAME_MAX = 255                    # maximum length of a file name


def gethostname():
    """The host name"""
    hostname = os.environ.get('TMDAHOST') or \
               os.environ.get('QMAILHOST') or \
               os.environ.get('MAILHOST')
    if not hostname:
        hostname = socket.getfqdn()
    return hostname


def getfullname():
    """The user's personal name.  Default is an empty value."""
    fullname = os.environ.get('TMDANAME') or \
               os.environ.get('QMAILNAME') or \
               os.environ.get('NAME') or \
               os.environ.get('MAILNAME')
    if not fullname:
        import pwd
        fullname = pwd.getpwuid(os.getuid())[4]
        if fullname:
            fullname = fullname.split(',')[0]
    return fullname


def getusername():
    """The user name"""
    username = os.environ.get('TMDAUSER') or \
               os.environ.get('QMAILUSER') or \
               os.environ.get('USER') or \
               os.environ.get('LOGNAME')
    if not username:
        import pwd
        username = pwd.getpwuid(os.getuid())[0]
    if not username:
        username = '<unknown>'
    return username


def getuid(username):
    """Return username's numerical user ID."""
    import pwd
    return pwd.getpwnam(username)[2]


def getgid(username):
    """Return username's numerical group ID."""
    import pwd
    return pwd.getpwnam(username)[3]


def gethomedir(username):
    """Return the home directory of username."""
    import pwd
    return pwd.getpwnam(username)[5]


def getgrouplist(username):
    """Read through the group file and calculate the group access
    list for the specified user.  Return a list of group ids."""
    import grp
    # calculate the group access list
    gids = [i[2] for i in grp.getgrall() if username in i[-1]]
    # include the base gid
    gids.insert(0, getgid(username))
    return gids


def getfilemode(path):
    """Return the octal number of the bit pattern for the file
    permissions on path."""
    statinfo = os.stat(path)
    permbits = stat.S_IMODE(statinfo[stat.ST_MODE])
    mode = int(oct(permbits))
    return mode


def getfileuid(path):
    """Return the numerical UID of the user owning the file in path."""
    statinfo = os.stat(path)
    return statinfo[stat.ST_UID]


def issticky(path):
    """Return True if the sticky bit is set on path.  Generally only
    appropriate for directories."""
    statinfo = os.stat(path)
    return statinfo[stat.ST_MODE] & stat.S_ISVTX


def getvdomainprepend(address, vdomainsfile):
    ret_prepend = ''
    if os.path.exists(vdomainsfile):
        fp = open(vdomainsfile, 'r')
        # Parse the virtualdomains control file; see qmail-send(8) for
        # syntax rules.  All this because qmail doesn't store the original
        # envelope recipient in the environment.
        u, d = address.split('@', 1)
        ousername = u.lower()
        odomain = d.lower()
        for line in fp.readlines():
            vdomain_match = 0
            line = line.strip().lower()
            # Comment or blank line?
            if line == '' or line[0] in '#':
                continue
            vdomain, prepend = line.split(':', 1)
            # domain:prepend
            if vdomain == odomain:
                vdomain_match = 1
            # .domain:prepend (wildcard)
            elif vdomain[:1] == '.' and odomain.find(vdomain) != -1:
                vdomain_match = 1
            # user@domain:prepend
            else:
                try:
                    if vdomain.split('@', 1)[1] == odomain:
                        vdomain_match = 1
                except IndexError:
                    pass
            if vdomain_match:
                ret_prepend = prepend
                break
        fp.close()
    return ret_prepend


def getvuserhomedir(user, domain, script):
    """Return the home directory of a qmail virtual domain user."""
    cmd = "%s %s %s" % (script, user, domain)
    fpin = os.popen(cmd)
    vuserhomedir = fpin.read()
    fpin.close()
    return vuserhomedir.strip()


def getuserparams(login):
    "Return a user's home directory, UID, & GID."
    import pwd
    stats = pwd.getpwnam(login)
    return (stats[5], stats[2], stats[3])


def RunTask(Args):
    """Run a program the "hard way" so we don't lose our UID."""

    # Open a pipe between the parent and a child process
    Read, Write = os.pipe()
    if not os.fork():
        # Child writes only and can close the reader
        os.close(Read)

        # Capture the STDOUT and stick it in the pipe
        os.dup2(Write, 1)

        # Launch the program
        os.execv(Args[0], Args)

    # Parent reads only and can close the writer
    os.close(Write)

    # Capture contents of pipe
    Read = os.fdopen(Read)
    RetVal = Read.readlines()
    Read.close()

    return RetVal


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
    import Defaults
    timeout = num + " " + Defaults.TIMEOUT_UNITS[unit]
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
    asctime_list = time.asctime(timetuple).split()
    asctime_list.insert(len(asctime_list)-1, tzname)
    return ' '.join(asctime_list)


def make_msgid(timesecs=None, pid=None):
    """Return an rfc2822 compliant Message-ID: string, composed of
    seconds since the epoch in UTC + process id + 'TMDA' + FQDN. e.g:

    <1016659379.10104.TMDA@nightshade.la.mastaler.com>

    timesecs is optional, and if not given, the current time is used.

    pid is optional, and if not given, the current process id is used.
    """
    if not timesecs:
        timesecs = time.time()
    if not pid:
        import Defaults
        pid = Defaults.PID
    idhost = os.environ.get('TMDAIDHOST') or \
             os.environ.get('QMAILIDHOST') or \
             gethostname()
    idtag = os.environ.get('TMDAIDTAG') or 'TMDA'
    msgid = '<%s.%s.%s@%s>' % (int(timesecs), pid, idtag, idhost)
    return msgid


def make_date(timesecs=None):
    """Return an RFC 2822 compliant Date string relative to the local
    timezone.  e.g,

    Tue, 02 Mar 2004 15:55:05 +1300

    timesecs is optional, and if not given, the current time is used.
    """
    if timesecs is None:
        timesecs = time.time()
    return email.utils.formatdate(timesecs, localtime=True)


def file_to_dict(file, dict):
    """Process and add then each line of a textfile to a dictionary."""
    for line in fileinput.input(file):
        line = line.strip()
        # Comment or blank line?
        if line == '' or line[0] in '#':
            continue
        else:
            fields = line.split()
            key = fields[0]
            key = key.lower()
            value = fields[1]
            dict[key] = value
    return dict


def file_to_list(file):
    """Process and then append each line of file to list."""
    list = []
    for line in fileinput.input(file):
        line = line.strip()
        # Comment or blank line?
        if line == '' or line[0] in '#':
            continue
        else:
            line = line.expandtabs().split('#')[0].strip()
            list.append(line)
    return list


def pipecmd(command, *strings):
    """Run a child process, returning opened pipes for communication.

    command is the program to execute as a sub-process.

    *strings are optional pieces of data to write to command.

    return_status will just return the exit status of the command..

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
            line = line.strip().lower()
            # Comment or blank line?
            if line == '' or line[0] in '#':
                continue
            else:
                line = line.expandtabs().split('#')[0].strip()
                bare = str.expandtabs().split('#')[0].strip()
                if bare.lower() == line:
                    fileinput.close()
                    return 0
    file = open(fullpathname, 'a+')
    file.write(str.strip() + '\n')
    file.close()


def pager(str):
    """Display a string using a UNIX text pager such as less or more."""
    pager = os.environ.get('PAGER')
    if pager is None:
        # try to locate less or more if $PAGER is not set
        for prog in ('less', 'more'):
            path = os.popen('which ' + prog).read()
            if path <> '':
                pager = path
                break
    try:
	os.popen(pager, 'w').write(str)
    except IOError:
	return


def normalize_sender(sender):
    """Return a normalized version of the given sender address for use
    in ~/.tmda/responses.

    - Any / characters are replaced with : to prevent creation of files
      outside the directory.
    - Spaces are replaced with underscores.
    - The address is lowercased.
    - Truncate sender at 233 chars to insure the full filename
    (including time, pid, and two dots) fits within the POSIX limit of
    255 chars for a filename.
    """
    sender = sender.replace(' ', '_')
    sender = sender.replace('/', ':')
    sender = sender.lower()
    return sender[:POSIX_NAME_MAX - 22]


def confirm_append_address(xp, rp):
    """
    xp is an address from the ``X-Primary-Address'' header.
    rp is the envelope sender address.

    Compare the two addresses, and return the address appropriate for
    CONFIRM_APPEND based on the PRIMARY_ADDRESS_MATCH setting.
    """
    if not xp:
        return rp
    if '@' not in rp or '@' not in xp:
        return rp
    import Defaults
    rpl = rp.lower()
    xpl = xp.lower()
    rplocal, rphost = rpl.split('@', 1)
    rpdomain = '.'.join(rphost.split('.')[-2:])
    rpusername = rplocal.split(Defaults.RECIPIENT_DELIMITER)[0]
    xplocal, xphost = xpl.split('@', 1)
    xpdomain = '.'.join(xphost.split('.')[-2:])
    xpusername = xplocal.split(Defaults.RECIPIENT_DELIMITER)[0]
    match = Defaults.PRIMARY_ADDRESS_MATCH
    if match == 0:
        # never a match
        return rp
    elif match == 1:
        # only identical addresses match
        if xpl == rpl:
            return xp
    elif match == 2:
        # usernames and hostnames must match
        if xpusername == rpusername and xphost == rphost:
            return xp
    elif match == 3:
        # usernames and domains must match
        if xpusername == rpusername and xpdomain == rpdomain:
            return xp
    elif match == 4:
        # hostnames must match
        if xphost == rphost:
            return xp
    elif match == 5:
        # domains must match
        if xpdomain == rpdomain:
            return xp
    elif match == 6:
        # always a match
        return xp
    return rp


def msg_from_file(fp, fullParse=False):
    """Read a file and parse its contents into a Message object model.
    Replacement for email.message_from_file().
    
    We use the HeaderParser subclass instead of Parser to avoid trying
    to parse the message body, instead setting the payload to the raw
    body as a string.  This is faster, and also helps us avoid
    problems trying to parse spam with broken MIME bodies."""
    from email.message import Message
    if fullParse:
	from email.parser import Parser
	msg = Parser(Message).parse(fp)
    else:
	from email.parser import HeaderParser
	msg = HeaderParser(Message).parse(fp)
    #msg.header_parsed = True
    return msg


def msg_as_string(msg, maxheaderlen=False, mangle_from_=False, unixfrom=False):
    """A more flexible replacement for Message.as_string().  The default
    is a textual representation of the message where the headers are
    not wrapped, From is not escaped, and a leading From_ line is not
    added.

    msg is an email.message.Message object.

    maxheaderlen specifies the longest length for a non-continued
    header.  Disabled by default.  RFC 2822 recommends 78.
    
    mangle_from_ escapes any line in the body that begins with "From"
    with ">".  Useful when writing to Unix mbox files.  Default is
    False.

    unixfrom forces the printing of the envelope header delimiter.
    Default is False."""
    from email import generator
    fp = StringIO()
    #if hasattr(msg, 'header_parsed') and msg.header_parsed:
    #    genclass = Generator.HeaderParsedGenerator
    #else:
         #genclass = Generator.Generator
    genclass = generator.Generator
    g = genclass(fp, mangle_from_=mangle_from_, maxheaderlen=maxheaderlen)
    g.flatten(msg, unixfrom=unixfrom)
    return fp.getvalue()


def sendmail(msgstr, envrecip, envsender):
    """Send e-mail via direct SMTP, or by opening a pipe to the
    sendmail program.

    msgstr is an rfc2822 message as a string.

    envrecip is the envelope recipient address.

    envsender is the envelope sender address.
    """
    import Defaults
    # Sending mail with a null envelope sender address <> is not done
    # the same way across the different supported MTAs, nor across the
    # two mail transports (SMTP and /usr/sbin/sendmail).
    #
    # The most common method is to use the string '<>'.  There are two
    # exceptions where an empty string must be used instead.
    #
    # 1) When running qmail/courier and using the sendmail transport.
    # qmail munges the envelope sender address into <"<>"@domain.dom
    # if "sendmail -f <>" is used.
    #
    # 2) When running Postfix and using the sendmail transport.
    # Old versions of Postfix apparently also have trouble with
    # "sendmail -f <>", though Postfix 2.0.x does not.
    if envsender == '':
        envsender = '<>'
    if envsender == '<>' and \
           Defaults.MAIL_TRANSFER_AGENT in ('postfix', 'qmail') and \
           Defaults.MAIL_TRANSPORT == 'sendmail':
        envsender = ''
    if Defaults.MAIL_TRANSPORT == 'sendmail':
        # You can avoid the shell by passing a tuple of arguments as
        # the command instead of a string.  This will cause the
        # popen2.Popen3() code to execvp() "/usr/bin/sendmail" with
        # these arguments exactly, with no trip through any shell.
        cmd = (Defaults.SENDMAIL_PROGRAM, '-i',
               '-f', envsender, '--', envrecip)
        pipecmd(cmd, msgstr)
    elif Defaults.MAIL_TRANSPORT == 'smtp':
        import SMTP
        server = SMTP.Connection()
        server.sendmail(envsender, envrecip, msgstr)
        server.quit()
    else:
        raise Errors.ConfigError, \
              "Invalid MAIL_TRANSPORT method: " + Defaults.MAIL_TRANSPORT


def decode_header(str):
    """Accept a possibly encoded message header as a string, and
    return a decoded string if it can be decoded.

    JRM: email.header has a decode_header method, but it returns a
    list of decoded pairs, one for each part of the header, which is
    an awkward interface IMO, especially when the header contains a
    mix of encoded and non-encoded parts.
    """
    try:
        from email import header
        parts = []
        pairs = header.decode_header(str)
        for pair in pairs:
            parts.append(pair[0])
        decoded_string = ' '.join(parts)
        return decoded_string
    except email.errors.HeaderParseError:
        return str


def headers_as_list(msg):
    """Return a list containing the entire set of header lines, in the
    order in which they were read."""
    return ['%s: %s' % (k, v) for k, v in msg.items()]


def headers_as_raw_string(msg):
    """Return the headers as a raw (undecoded) string."""
    msgtext = msg_as_string(msg)
    idx = msgtext.index('\n\n')
    return msgtext[:idx+1]


def headers_as_string(msg):
    """Return the (decoded) message headers as a string.  If the
    sequence can't be decoded, punt and return a raw (undecoded)
    string instead."""
    try:
        hdrstr = '\n'.join(['%s: %s' %
                            (k, decode_header(v)) for k, v in msg.items()])
    except email.errors.HeaderParseError:
        hdrstr = headers_as_raw_string(msg)
    return hdrstr


def body_as_raw_string(msg):
    """Return the body as a raw (undecoded) string."""
    msgtext = msg_as_string(msg)
    idx = msgtext.index('\n\n')
    return msgtext[idx+2:]



def rename_headers(msg, old, new):
    """Rename all occurances of a message header in a Message object.

    msg is an email.message.Message object.

    old is name of the header to rename.

    new is the new name of the header
    """
    if msg.has_key(old):
        for pair in msg._headers:
            if pair[0].lower() == old.lower():
                index = msg._headers.index(pair)
                msg._headers[index] = (new, '%s' % pair[1])


def add_headers(msg, headers):
    """Add headers to a Message object.

       msg is an email.message.Message object.

       headers is a dictionary of headers and values.
       """
    if headers:
        keys = headers.keys()
        keys.sort()
        for k in keys:
            del msg[k]
            msg[k] = headers[k]


def purge_headers(msg, headers):
    """Purge headers from a Message object.

       msg is an email.message.Message object.

       headers is a list of headers.
       """
    if headers:
        for h in headers:
            del msg[h]


def build_cdb(filename):
    """Build a cdb file from a text file."""
    import cdb
    try:
        cdbname = filename + '.cdb'
        tempfile.tempdir = os.path.dirname(filename)
        tmpname = os.path.split(tempfile.mktemp())[1]
        cdb = cdb.cdbmake(cdbname, cdbname + '.' + tmpname)
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
    """Build a DBM file from a text file."""
    import anydbm
    import glob
    try:
        dbmpath, dbmname = os.path.split(filename)
        dbmname += '.db'
        tempfile.tempdir = dbmpath
        tmpname = tempfile.mktemp()
        dbm = anydbm.open(tmpname, 'n')
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
            newf = f.replace(tmpname, dbmname)
            newf = os.path.join(tmppath, newf)
            os.rename(f, newf)
    except:
        return 0
    else:
        return 1


def pickleit(object, file, proto=2):
    """Store object in a pickle file.

    Optional 'proto' specifies which data storage format to use.
    Possible integer values include:

    0 (original ASCII protocol and is backwards compatible with
    earlier versions of Python)

    1 (old binary format which is also compatible with earlier
    versions of Python)

    2 (a more effecient binary format introduced in Python 2.3)

    -1 (always choose the highest protocol version available)

    default is 2, since we must support Python 2.3 and above.
    """
    tempfile.tempdir = os.path.dirname(file)
    tmpname = tempfile.mkstemp()[1]
    fp = open(tmpname, 'w')
    cPickle.dump(object, fp, proto)
    fp.close()
    os.rename(tmpname, file)
    return


def unpickle(file):
    """Retrieve and return object from file."""
    fp = open(file, 'r')
    object = cPickle.load(fp)
    fp.close()
    return object


def db_insert(db, insert_sql, params):
    """Insert (using the 'insert_sql' SQL) an address into a SQL DB."""
    dbmodule = sys.modules[db.__module__]
    DatabaseError = getattr(dbmodule, 'DatabaseError')
    cursor = db.cursor()
    try:
        try:
            cursor.execute(insert_sql, params)
            db.commit()
        except DatabaseError:
            pass
    finally:
        cursor.close()


def findmatch(list, addrs):
    """Determine whether any of the passed e-mail addresses match a
    Unix shell-style wildcard pattern contained in list.  The
    comparison is case-insensitive.  Also, return the second half of
    the string if it exists (for exp and ext addresses only)."""
    for address in addrs:
        if address:
            address = address.lower()
            for p in list:
                stringparts = p.split()
                p = stringparts[0]
                # Handle special @=domain.dom syntax.
                try:
                    at = p.rindex('@')
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


def wraptext(text, column=70):
    """Wrap and fill the text to the specified column width."""
    wrapper = textwrap.TextWrapper(width=column, break_long_words=False)
    return wrapper.fill(text)


def maketext(templatefile, vardict):
    """Make some text from a template file.

    templatefile can either be an absolute pathname starting with an /
    or ~ (e.g, /usr/local/packages/tmda/templates/bounce.txt) or a
    relative pathname (e.g, bounce.txt).

    Given a relative pathname, several locations are scanned for
    templatefile, in the following order:

    1. The directory specified by tmda-filter's `-t' option.
    2. Defaults.TEMPLATE_DIR_MATCH_SENDER (if true)
    3. Defaults.TEMPLATE_DIR_MATCH_RECIPIENT (if true)
    4. Defaults.TEMPLATE_DIR
    5. ../templates/
    6. The package/RPM template directories.

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
    foundit = None
    if (templatefile[0] == '/' or templatefile[0] == '~'):
        if templatefile[0] == '~':
            templatefile = os.path.expanduser(templatefile)
        if os.path.exists(templatefile):
            foundit = templatefile
    else:
        # Calculate the locations to scan.
        searchdirs = []
        searchdirs.append(os.environ.get('TMDA_TEMPLATE_DIR'))
        if Defaults.TEMPLATE_DIR_MATCH_SENDER and Defaults.TEMPLATE_DIR:
            sender = os.environ.get('SENDER').lower()
            searchdirs.append(os.path.join(Defaults.TEMPLATE_DIR, sender))
            try:
                domainparts = sender.split('@', 1)[1].split('.')
                for i in range(len(domainparts)):
                    searchdirs.append(os.path.join
                                      (Defaults.TEMPLATE_DIR, '.'.join(domainparts)))
                    del domainparts[0]
            except IndexError:
                pass
        if Defaults.TEMPLATE_DIR_MATCH_RECIPIENT and Defaults.TEMPLATE_DIR:
            recipient = os.environ.get('TMDA_RECIPIENT').lower()
            searchdirs.append(os.path.join(Defaults.TEMPLATE_DIR, recipient))
            try:
                recippart, domainpart = recipient.split('@',1)
                recipparts = recippart.split(Defaults.RECIPIENT_DELIMITER)
                for i in range(len(recipparts)):
                    searchdirs.append(os.path.join
                                      (Defaults.TEMPLATE_DIR,
                                       Defaults.RECIPIENT_DELIMITER.join(recipparts) +
                                       "@" + domainpart))
                    del recipparts[-1]
                domainparts = domainpart.split('.')
                for i in range(len(domainparts)):
                    searchdirs.append(os.path.join
                                      (Defaults.TEMPLATE_DIR, '.'.join(domainparts)))
                    del domainparts[0]
            except IndexError:
                pass
        searchdirs.append(Defaults.TEMPLATE_DIR)
        searchdirs.append(os.path.join(Defaults.PARENTDIR, 'templates'))
        searchdirs.append(os.path.join(sys.prefix, 'share/tmda'))
        searchdirs.append('/etc/tmda/')
        # Start scanning.
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
    import Defaults
    import FilterParser
    filter = FilterParser.FilterParser(Defaults.DB_CONNECTION)
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


def CanRead( file, uid = None, gid = None, raiseError = 1 ):
    try:
        return CanMode( file, MODE_READ, uid, gid )
    except IOError:
        if not raiseError:
            return 0
        else:
            pass


def CanWrite( file, uid = None, gid = None, raiseError = 1 ):
    try:
        return CanMode( file, MODE_WRITE, uid, gid )
    except IOError:
        if not raiseError:
            return 0
        else:
            pass


def CanExec( file, uid = None, gid = None, raiseError = 1 ):
    try:
        return CanMode( file, MODE_EXEC, uid, gid )
    except IOError:
        if not raiseError:
            return 0
        else:
            pass


def CanMode( file, mode = MODE_READ, uid = None, gid = None ):
    try:
        fstat = os.stat( file )
    except:
        raise IOError, "'%s' does not exist" % file
    if uid is None:
        uid = os.geteuid()
    if gid is None:
        gid = os.getegid()
    needuid = fstat[4]
    needgid = fstat[5]
    filemod = fstat[0] & 0777
    if uid == 0:
        # Root always wins.
        return 1
    elif filemod & mode:
        return 1
    elif filemod & ( mode * 010 ) and needgid == gid:
        return 1
    elif filemod & ( mode * 0100 ) and needuid == uid:
        return 1
    else:
        return 0


class DevnullOutput:
    def write(self, msg): pass
    def flush(self): pass
    def __repr__(self):
        return ""


class StringOutput:
    def __init__(self):
        self.__content = ""
    def write(self, msg):
        if msg != "":
            self.__content += "%s" % msg
    def flush(self):
        self.__content = ""
    def __repr__(self):
        return self.__content


class Debugable:
    def __init__(self, outputObject = DevnullOutput() ):
        self.DEBUGSTREAM = outputObject
        if self.DEBUGSTREAM is DevnullOutput:
            self.level = 0
        else:
            self.level = 1

    def debug(self, msg, level = 1):
        if self.level >= level:
            print >> self.DEBUGSTREAM, msg

    def set_debug(level = 1):
        self.level = level

    def set_nodebug():
        self.level = 0

