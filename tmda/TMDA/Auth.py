# -*- python -*-
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
#
# Author: David Guerizec <david@guerizec.net>
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

"""Authentication functions."""


import os
import sys
import time

import Version
import Util
import Errors

## FIXME: debug stuff should be in it's own module
class Devnull:
    def write(self, msg): pass
    def flush(self): pass

DEBUGSTREAM = Devnull()
#####



program = sys.argv[0]
authprog = None
remoteauth = { 'proto': None,
               'host':  'localhost',
               'port':  None,
               'dn':  '',
               'enable': 0,
               }
defaultauthports = { 'imap':  143,
                     'imaps': 993,
                     'apop': 110,
                     'pop3':  110,
                     'ldap':  389,
                     #                     'pop3s': 995,
                     }

if os.getuid() == 0:
    running_as_root = 1
else:
    running_as_root = 0

if running_as_root:
    username = 'tofmipd'
    authfile = '/etc/tofmipd'
else:
    username = None
    authfile = os.path.join(os.path.expanduser('~'), '.tmda', 'tofmipd')

authtype = 'file'

def warning(msg='', exit=1):
    delimiter = '*' * 70
    if msg:
        msg = Util.wraptext(msg)
        print >> sys.stderr, '\n', delimiter, '\n', msg, '\n', delimiter, '\n'
    if exit:
        sys.exit()

# check whether we are running a recent enough Python
if not Version.PYTHON >= '2.2':
    msg = 'Python 2.2 or greater is required to run ' + program + \
          ' -- Visit http://python.org/download/ to upgrade.'
    warning(msg)


def security_disclaimer():
    # provide disclaimer if running as root
    if running_as_root:
        msg = 'WARNING: The security implications and risks of running ' + \
              program + ' in "seteuid" mode have not been fully evaluated.  ' + \
              'If you are uncomfortable with this, quit now and instead run ' + \
              program + ' under your non-privileged TMDA user account.'
        warning(msg, exit=0)
    
def parse_auth_uri(arg):
    # arg is like: imap://host:port
    try:
        authproto, arg = arg.split('://', 1)
    except ValueError:
        authproto, arg = arg, None
    remoteauth['proto'] = authproto
    remoteauth['port'] = defaultauthports[authproto]
    if authproto not in defaultauthports.keys():
        raise ValueError, 'Protocol not supported: ' + authproto + \
                '\nPlease pick one of ' + repr(defaultauthports.keys())
    if arg:
        try:
            arg, dn = arg.split('/', 1)
            remoteauth['dn'] = dn
        except ValueError:
            dn = ''
        try:
            authhost, authport = arg.split(':', 1)
        except ValueError:
            authhost = arg
            authport = defaultauthports[authproto]
        if authhost:
            remoteauth['host'] = authhost
        if authport:
            remoteauth['port'] = authport
    print >> DEBUGSTREAM, "auth method: %s://%s:%s/%s" % \
          (remoteauth['proto'], remoteauth['host'],
           remoteauth['port'], remoteauth['dn'])
    remoteauth['enable'] = 1


import socket

import asynchat
import asyncore
import base64
import hmac
import md5
import popen2
import random
import time


__version__ = Version.TMDA

def init_auth_method():
    global IMAP4_SSL
    if remoteauth['proto'] == 'imaps':
        vmaj, vmin = sys.version_info[:2]
        # Python version 2.2 and before don't have IMAP4_SSL
        import imaplib
        if vmaj <= 2 or (vmaj == 2 and vmin <= 2):
            class IMAP4_SSL(imaplib.IMAP4):
                # extends IMAP4 class to talk SSL cause it's not yet
                # implemented in python 2.2
                def open(self, host, port):
                    """Setup connection to remote server on "host:port".
                    This connection will be used by the routines:
                    read, readline, send, shutdown.
                    """
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.host, self.port))
                    self.sslsock = socket.ssl(self.sock)
                    self.file = self.sock.makefile('rb')
            
                def read(self, size):
                    """Read 'size' bytes from remote."""
                    buf = self.sslsock.read(size)
                    return buf
            
                def readline(self):
                    """Read line from remote."""
                    line = [ ]
                    c = self.sslsock.read(1)
                    while c:
                        line.append(c)
                        if c == '\n':
                            break
                        c = self.sslsock.read(1)
                    buf = ''.join(line)
                    return buf
            
                def send(self, data):
                    """Send data to remote."""
                    bytes = len(data)
                    while bytes > 0:
                        sent = self.sslsock.write(data)
                        if sent == bytes:
                            break   # avoid copy
                        data = data[sent:]
                        bytes = bytes - sent
        else:
            IMAP4_SSL = imaplib.IMAP4_SSL
    
    if remoteauth['proto'] == 'ldap':
        try:
            import ldap
        except ImportError:
            raise ImportError, \
                  'python-ldap (http://python-ldap.sf.net/) required.'
        if remoteauth['dn'] == '':
            print >> DEBUGSTREAM, "Error: Missing ldap dn\n"
            raise ValueError
        try:
            remoteauth['dn'].index('%s')
        except:
            print >> DEBUGSTREAM, "Error: Invalid ldap dn\n"
            raise ValueError


# Utility functions
def pipecmd(command, *strings):
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
    return cmd.wait()


def run_authprog(username, password):
    """authprog should return 0 for auth ok, and a positive integer in
    case of a problem.  Return 1 upon successful authentication, and 0
    otherwise."""
    print >> DEBUGSTREAM, "Trying authprog method"
    cmd = "/bin/sh -c 'exec %s 3<&0'" % authprog
    authResult = pipecmd(cmd, '%s\0%s\0' % (username, password))
    print >> DEBUGSTREAM, "'%s' returned %d" % (authprog, authResult)
    return authResult == 0

def run_remoteauth(username, password):
    """Authenticate username/password combination against a remote
    resource.  Return 1 upon successful authentication, and 0
    otherwise."""
    print >> DEBUGSTREAM, "trying %s authentication for %s@%s:%s" % \
          (remoteauth['proto'], username, remoteauth['host'],
           remoteauth['port'])
    port = defaultauthports[remoteauth['proto']]
    if remoteauth['proto'] == 'imap':
        import imaplib
        if remoteauth['port']:
            port = int(remoteauth['port'])
        M = imaplib.IMAP4(remoteauth['host'], port)
        try:
            (type, data) = M.login(username, password)
            print >> DEBUGSTREAM, "Login response: %s %s" % (type, data)
            retVal = ( type == 'OK' )
            (type, data) = M.logout()
            print >> DEBUGSTREAM, "Logout response: %s %s" % (type, data)
            return retVal
        except IMAP4.error, err:
            print >> DEBUGSTREAM, "imap authentication for %s@%s failed" % \
                  (username, remoteauth['host'], err)
            return 0
    elif remoteauth['proto'] == 'imaps':
        import imaplib
        if remoteauth['port']:
            port = int(remoteauth['port'])
        M = IMAP4_SSL(remoteauth['host'], port)
        try:
            (type, data) = M.login(username, password)
            print >> DEBUGSTREAM, "Login response: %s %s" % (type, data)
            retVal = ( type == 'OK' )
            M.logout()
            (type, data) = M.logout()
            print >> DEBUGSTREAM, "Logout response: %s %s" % (type, data)
            return retVal
        except IMAP4_SSL.error, err:
            print >> DEBUGSTREAM, "imaps authentication for %s@%s failed: %s" % \
                  (username, remoteauth['host'], err)
            return 0
    elif remoteauth['proto'] in ('pop3', 'apop'):
        import poplib
        if remoteauth['port']:
            port = int(remoteauth['port'])
        M = poplib.POP3(remoteauth['host'], port)
        try:
            if remoteauth['proto'] == 'pop3':
                M.user(username)
                M.pass_(password)
                M.quit()
                return 1
            else:
                M.apop(username, password)
                M.quit()
                return 1
        except poplib.error_proto, err:
            print >> DEBUGSTREAM, "%s authentication for %s@%s failed: %s" % \
                  (remoteauth['proto'], username, remoteauth['host'], err)
            return 0
    elif remoteauth['proto'] == 'ldap':
        import ldap
        if remoteauth['port']:
            port = int(remoteauth['port'])
        try:
            M = ldap.initialize("ldap://%s:%s" % (remoteauth['host'],
                                                  remoteauth['port']))
            M.simple_bind_s(remoteauth['dn'] % username, password)
            M.unbind_s()
            return 1
        except:
            print >> DEBUGSTREAM, "ldap authentication for %s@%s failed" % \
                  (username, remoteauth['host'])
            return 0
    # proto not implemented
    print >> DEBUGSTREAM, "Error: protocol %s not implemented" % \
            remoteauth['proto']
    return 0

def authenticate_plain(username, password, type=None):
    if type == None:
        type = authtype
    try:
      if type == 'remote':
          return run_remoteauth(username, password)
      if type == 'prog':
          return run_authprog(username, password)
      if type == 'file':
          ## FIXME: implement /etc/tofmipd auth
          return 0
    except:
      return 0
    
    raise Errors.AuthError, \
      "Unknown authentication type '%s'." % type, \
      "Ensure that Auth.authtype is set to 'remote' 'prog' or 'file'"

def authfile2dict(authfile):
    """Iterate over a tmda-ofmipd authentication file, and return a
    dictionary containing username:password pairs.  Username is
    returned in lowercase."""
    authdict = {}
    fp = file(authfile, 'r')
    for line in fp:
        line = line.strip()
        if line == '':
            continue
        else:
            fields = line.split(':', 1)
            authdict[fields[0].lower().strip()] = fields[1].strip()
    fp.close()
    return authdict


def b64_encode(s):
    """base64 encoding without the trailing newline."""
    return base64.encodestring(s)[:-1]


def b64_decode(s):
    """base64 decoding."""
    return base64.decodestring(s)

def auth_fork(auth_username):
    # If running as uid 0, fork the tmda-inject process, and
    # then change UID and GID to the authenticated user.
    if running_as_root:
        pid = os.fork()
        if pid == 0:
            os.seteuid(0)
            os.setgid(Util.getgid(auth_username))
            os.setgroups(Util.getgrouplist(auth_username))
            os.setuid(Util.getuid(auth_username))
            # This is so "~" will work in the .tmda/* files.
            os.environ['HOME'] = Util.gethomedir(auth_username)
            # This is so addresses will be generated with the good
            # username
            os.environ['USER'] = auth_username
            return 0
        else:
            rpid, status = os.wait()
            if status != 0:
                raise IOError, 'it seems that user %s experienced problems!' \
                               % auth_username
            return 1
    return 0


pw_uid = None

def check_authfile_owner(username):
    global pw_uid
    # check permissions of authfile
    authfile_mode = Util.getfilemode(authfile)
    if authfile_mode not in (400, 600):
        raise IOError, \
              authfile + ' must be chmod 400 or 600!'
    if running_as_root:
        pw_uid = Util.getuid(username)
        # check ownership of authfile
        if Util.getfileuid(authfile) != pw_uid:
            raise IOError, \
                  authfile + ' must be owned by UID ' + str(pw_uid)

def seteuid(username):
    if running_as_root:
        if pw_uid is None:
            check_authfile_owner(username)
        # try setegid()
        os.setegid(Util.getgid(username))
        # try setting the supplemental group ids
        os.setgroups(Util.getgrouplist(username))
        # try seteuid()
        os.seteuid(pw_uid)


