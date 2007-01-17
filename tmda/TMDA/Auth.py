# -*- python -*-
#
# Copyright (C) 2001-2007 Jason R. Mastaler <jason@mastaler.com>
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

# System imports
import base64
import hmac
import imaplib
import md5
import os
import popen2
import poplib
import socket
import sys
import time

# TMDA imports
import Version
import Util
import Errors

class Auth(Util.Debugable):
    """Authentication mechanisms for TMDA"""

    def __init__(self, authtype=None, autharg=None, \
                 configdir = None, \
                 vuser = None, vlookupscript = None, \
                 ipauthmapfile = None, localip = "127.0.0.1",
                 debugObject = Util.DevnullOutput() ):
        """Setup initial values.
        Optional: authtype and autharg initialize the authentication mechanism
                  configdir to set an alternate directory to /home/user
                    (tmda dir will be configdir/.tmda/ )
                  vlookupscript and vuser for virtual users
                  debugObject to begin debugging immediately
        """
        Util.Debugable.__init__(self, debugObject)

        # Internal vars
        self.__version__ = Version.TMDA
        self.__program = sys.argv[0]
        self.__authprog = None
        self.__authdict = None
        self.__authdictupdate = None
        self.__authremote = { 'proto': None,
                              'host':  'localhost',
                              'port':  None,
                              'dn':  '',
                              'enable': 0,
                            }
        self.__defaultauthports = { 'imap':  143,
                                    'imaps': 993,
                                    'apop':  110,
                                    'pop3':  110,
                                    'ldap':  389,
                                    #'pop3s': 995,
                                  }

        self.__ownerID = os.getuid()
        if self.__ownerID == 0:
            self.running_as_root = 1
        else:
            self.running_as_root = 0

        # Default values
        self.__default_auth_filename = "tmdauth"
        self.__default_owner_username = "tmdauth"
        self.__default_tmda_dir = ".tmda"
        self.__system_tmda_path = "/etc"
        self.__owner_tmda_path = self.__system_tmda_path
        self.__owner_username = None
        if self.running_as_root:
            self.__owner_username = self.__default_owner_username
        elif os.environ.has_key("HOME"):
            self.__owner_tmda_path = os.path.join(os.path.expanduser('~'), \
                                                  self.__default_tmda_dir)
        self.__defaultauthfile = os.path.join(self.__owner_tmda_path, \
                                              self.__default_auth_filename)
        self.__defaultipauth = os.path.join(self.__owner_tmda_path, 'ipauthmap')
        if self.__owner_tmda_path != "/etc":
            if not Util.CanRead(self.__defaultauthfile, raiseError = 0):
                self.__defaultauthfile = os.path.join(self.__system_tmda_path, \
                                                      'tmdauth')
            if not Util.CanRead(self.__defaultipauth, raiseError = 0):
                self.__defaultipauth = os.path.join(self.__system_tmda_path, \
                                                    'ipauthmap')

        # external vars
        self.allowed_authtypes = ( 'file', 'checkpw', 'remote' )
        self.allowed_protocols = self.__defaultauthports.keys()

        # Initialize the authtype if possible
        if authtype is None:
            try:
                self.init_auth_method( 'file', self.__defaultauthfile )
            except ValueError:
                self.__authtype = "Undefined"
        else:
            self.init_auth_method( authtype, autharg ) 

        # Set up the ipauthmapfile
        if ipauthmapfile is not None:
            self.__ipauthmapfile = ipauthmapfile
        else:
            self.__ipauthmapfile = self.__defaultipauth
        self.__localip = localip

        # Initialize virtual users if necessary
        self.__use_confdir = 0
        self.__use_vhome = 0
        if vlookupscript is not None:
            self.setup_vuser( vlookupscript, vdomainfile )
        elif configdir is not None:
            self.setup_configdir( configdir )

    def warning(self, msg='', exit=1):
        delimiter = '*' * 70
        if msg:
            msg = Util.wraptext(msg)
            print >> sys.stderr, "%s Auth: %s" % (self.__program, msg)
        if exit:
            sys.exit()

    def security_disclaimer(self):
        # provide disclaimer if running as root
        if self.running_as_root:
            msg = 'WARNING: The security implications and risks of running ' + \
                  self.__program + ' in "seteuid" mode have not been fully ' + \
                  'evaluated.  If you are uncomfortable with this, quit now' + \
                  'and instead run' + self.__program + ' under your ' + \
                  'non-privileged TMDA user account.'
            self.warning(msg, exit=0)
    
    # Public Methods
    def init_auth_method(self, type, arg):
        """Initializes the authentication mechanism.
        See init_file, init_checkpw, and init_remote for more details.
        """
        mname = 'init_%s' % type
        meth = getattr(self, mname, None)
        if meth is None:
            self.debug("Attribute Error: " \
                       "Auth instance has no attribute '%s'" % mname)
            raise ValueError(
                "Authentication type '%s' not recognised.\n " \
                "Must be one of %s" % (type, repr(self.allowed_authtypes)))
        meth(arg)

    def init_file(self, file):
        """Initializes the authentication scheme with a flat file.
        - If the file has mode 400 or 600, it is allowed to contain cleartext
          passwords.
        - Otherwise it must contain encrypted passwords only.

        May raise ValueError if file does not exist.
        """
        if file is None:
            file = self.__defaultauthfile
        self.debug( "Setting up file authentication with file '%s'" % file )
        if not Util.CanRead(file, raiseError = 0):
            raise ValueError, "File '%s' does not exist" % file
        self.__authtype = "file"
        self.__authfile = file
        self.__authfile_allows_cleartext = Util.getfilemode(file) in (400, 600)
        self.__authdict = None
        self.__authdictupdate = None
        self.__update_authdict()

    def init_checkpw(self, checkpw):
        """Initializes the authentication scheme with a checkpw-style program.
        - If this checkpw string contains a space (and therefore arguments) we
          assume that it includes the "true" program in the proper spot for that
          program
        - Otherwise, we look to see if /usr/bin/true or /bin/true is available,
          and append that on the end.

        May raise ValueError for missing/not-executable checkpw
        """
        self.debug( "Setting up checkpw authentication with '%s'" % checkpw )
        try:
            # Separate out the "actual" checkpassword program
            realprogram, args = checkpw.split(" ", 1)
        except ValueError:
            # No space in "checkpw", try to figure out what to use as "true"
            realprogram = checkpw
            trueprog = "/usr/bin/true"
            if not Util.CanExec(trueprog, raiseError = 0):
                trueprog = "/bin/true"
                if not Util.CanExec(trueprog, raiseError = 0):
                    raise ValueError, \
                        "Could not locate /usr/bin/true or /bin/true.\n" + \
                        "Please supply this with the checkpassword program"
            args = trueprog
        # Make sure that checkpassword program exists and is executable.
        try:
            if not Util.CanExec(realprogram, self.__ownerID):
                raise ValueError, "Checkpassword program '%s'" % realprogram + \
                    " not executable by userid %d" % self.__ownerID
        except IOError:
            raise ValueError, "'%s' does not exist" % realprogram
        self.__authtype = 'checkpw'
        self.__authprog = "%s %s" % (checkpw, args)
        self.debug( "Auth program is '%s'" % self.__authprog )

    def init_remote(self, URI):
        """Initializes the authentication scheme with a remote URI.
        May raise ValueError for a bad URI
        """
        self.debug( "Setting up remote authentication with %s" % URI )
        self.__authremote['enable'] = 0
        # Default host = localhost
        self.__authremote["host"] = "localhost"
        try:
            authproto, arg = URI.split('://', 1)
        except ValueError:
            authproto, arg = URI, None
        if authproto not in self.allowed_protocols:
            raise ValueError, "Protocol '%s' not supported.\n" % authproto + \
                    "Must be one of %s" % repr(self.allowed_protocols)
        self.__authremote['proto'] = authproto
        self.__authremote['port'] = self.__defaultauthports[authproto]
        if arg:
            try:
                arg, dn = arg.split('/', 1)
                self.__authremote['dn'] = dn
            except ValueError:
                dn = ''
            try:
                authhost, authport = arg.split(':', 1)
            except ValueError:
                authhost, authport = arg, self.__defaultauthports[authproto]
            if authhost:
                self.__authremote['host'] = authhost
            if authport:
                self.__authremote['port'] = authport

        elif self.__authremote['proto'] == 'ldap':
            try:
                import ldap
            except ImportError:
                raise ValueError, \
                    "Ldap not supported: python-ldap " + \
                    "(http://python-ldap.sf.net/) required."
            if self.__authremote['dn'] == '':
                raise ValueError, \
                    "Missing ldap dn (format ldap://host[:port]/dn)"
            try:
                self.__authremote['dn'].index('%(user)s')
            except:
                raise ValueError, \
                    "Invalid ldap dn (must contain %%(user)s)"
        self.__authtype = "remote"
        self.__authremote['enable'] = 1

    def authenticate_plain(self, username, password):
        """Authenticates a cleartext username and password"""
        retval = 0
        try:
            cmd = "self.authenticate_plain_%s(username, password)" \
                    % self.__authtype
            retval = eval( cmd )
        except AttributeError:
            raise Errors.AuthError, \
                 ( "Unknown authentication type '%s'." % self.__authtype, \
                   "Available choices for authentication type are %s" % \
                    repr(self.allowed_authtypes) )
        except Errors.AuthError, err:
            raise err
        self.debug( "Authentication returned: %d" % retval )
        return retval

    def authenticate_base64(self, username, password):
        """Authenticates a base64-encoded username and password"""
        return self.authenticate_plain( self.__b64_decode(username),
                                        self.__b64_decode(password) )

    def authenticate_cram_md5(self, response, ticket, response_encoded = 1, \
                              digestmod = md5):
        """Authenticates a cram_md5 response based on a ticket.
           Expects a base-64 encoded "response" unless otherwise specified."""
        if not self.supports_cram_md5():
            raise Errors.AuthError, \
              ( "Cram MD5 authentication not supported.",\
                "Ensure that file authentication is being used, and check " + \
                "file permissions" )
        if response_encoded:
            try:
                response = self.__b64_decode( response )
            except:
                return 501
        try:
            username, hexdigest = response.split()
        except ValueError:
            return 0
        self.__update_authdict()
        password = self.__authdict.get(username.lower(), 0)
        if password == 0:
            return 0
        newhexdigest = hmac.HMAC(password, ticket, digestmod).hexdigest()
        return newhexdigest == hexdigest

    def supports_cram_md5(self):
        """Check if Cram MD5 authentication is supported.
           Requirements: "hmac" module, File authentication, 
                         and file allows cleartext passwords"""
        retval = 0
        try:
            import hmac
        except ImportError:
            return 0
        if self.__authtype == "file" and self.__authfile_allows_cleartext:
            retval = 1
        return retval

    def setup_vuser( self, vlookupscript ):
        self.__vlookupscript = vlookupscript
        self.__use_vhome = 1
        self.__use_confdir = 0

    def setup_configdir( self, configdir ):
        self.__configdir = configdir
        self.__use_confdir = 1
        self.__use_vhome = 0

    def get_homedir( username, domain = None ):
        if self.__use_configdir:
            return os.path.join( os.path.expanduser(self.__configdir), \
                                 username )
        elif self.__use_vhome:
            if domain is None:
                raise ValueError, "domain is requined for virtual users"
            return Util.getvuserhomedir(user, domain, self.__vlookupscript)
        else:
            return Util.gethomedir( username )

    def get_tmdadir( username, domain = None ):
        return os.path.join( self.get_homedir( username, domain ), \
                             self.__default_tmda_dir )

    # Private utility functions
    def authenticate_plain_file(self, username, password):
        """Checks authdict for the password.
        Return 1 for a match, 0 otherwise."""
        self.debug( "Trying file authentication with '%s'" % self.__authfile )
        import crypt
        self.__update_authdict()
        pw = self.__authdict.get(username.lower(), 0)
        if pw == 0:
            self.debug( "No user %s" % username.lower() )
            raise Errors.AuthError, \
                ( "User %s not found in password file" % username, \
                  "Ensure that this user exists in '%s'" % self.__authfile )
        if pw == "":
            self.debug( "Blank %s password" % username.lower() )
            raise Errors.AuthError, \
                ( "User %s is denied login" % username, \
                  "Blank password in file '%s'" % self.__authfile )
        self.debug( "Comparing encrypted password." )
        retval = crypt.crypt(password, pw[:2]) == pw
        if not retval and self.__authfile_allows_cleartext:
            self.debug( "Comparing un-encrypted password." )
            retval = password == pw
        return retval

    def authenticate_plain_checkpw(self, username, password):
        """The checkpassword program should return 0 for auth ok, and a positive
        integer in case of a problem.
        Return 1 upon successful authentication, 0 otherwise"""
        self.debug( "Trying checkpw method" )
        authResult = 0
        try:
            authResult = not self.__pipefd3( self.__authprog, \
                                             '%s\0%s\0' % (username, password) )
        except Exception, err:
            self.debug( "pipefd3 failed (%s: %s).\n" % (err.__class__, err) + \
                   "Falling back to /bin/sh redirection" )
            cmd = "/bin/sh -c 'exec %s 3<&0'" % self.__authprog
            authResult = not self.__pipecmd( cmd, \
                                             '%s\0%s\0' % (username, password) )
        return authResult

    def authenticate_plain_remote(self, username, password):
        """Authenticate username/password combination against a remote
        resource.  Return 1 upon successful authentication, and 0
        otherwise."""
        self.debug( "Trying %s authentication for %s@%s:%s" % \
              (self.__authremote['proto'], username, self.__authremote['host'],
               self.__authremote['port']) )
        # IPauthmapfile stuff:
        authhost = self.__authremote['host']
        authport = self.__authremote['port']
        if authhost == '0.0.0.0':
            ipauthmap = self.__ipauthmap2dict( self.__ipauthmapfile )
            if len( ipauthmap ) == 0:
                authhost = self.__localip
            else:
                authdata = ipauthmap.get(self.__localip, '127.0.0.1').split(':')
                authhost = authdata[0]
                if len(authdata) > 1:
                    authport = authdata[1]
            self.__authremote['host'] = authhost
            self.__authremote['port'] = authport
        port = self.__defaultauthports[self.__authremote['proto']]
        if self.__authremote['proto'] == 'imap':
            if self.__authremote['port']:
                port = int(self.__authremote['port'])
            M = imaplib.IMAP4(self.__authremote['host'], port)
            try:
                (type, data) = M.login(username, password)
                self.debug( "Login response: %s %s" % (type, data) )
                retVal = ( type == 'OK' )
                M.logout()
                return retVal
            except imaplib.IMAP4.error, err:
                self.debug( "imap authentication for %s@%s failed" % \
                      (username, self.__authremote['host']) )
                return 0
            except Exception, err:
                self.debug( "Uncaught %s: %s" % (err.__class__, err) )
                return 0
        elif self.__authremote['proto'] == 'imaps':
            if self.__authremote['port']:
                port = int(self.__authremote['port'])
            M = imaplib.IMAP4_SSL(self.__authremote['host'], port)
            try:
                (type, data) = M.login(username, password)
                self.debug( "Login response: %s %s" % (type, data) )
                retVal = ( type == 'OK' )
                M.logout()
                return retVal
            except Exception, err:
                self.debug( "imap authentication for %s@%s failed" % \
                      (username, self.__authremote['host']) )
                return 0
        elif self.__authremote['proto'] in ('pop3', 'apop'):
            if self.__authremote['port']:
                port = int(self.__authremote['port'])
            M = poplib.POP3(self.__authremote['host'], port)
            try:
                if self.__authremote['proto'] == 'pop3':
                    M.user(username)
                    M.pass_(password)
                    M.quit()
                    return 1
                else:
                    M.apop(username, password)
                    M.quit()
                    return 1
            except poplib.error_proto, err:
                self.debug( "%s authentication for %s@%s failed: %s" % \
                      (self.__authremote['proto'], username, \
                       self.__authremote['host'], err) )
                return 0
        elif self.__authremote['proto'] == 'ldap':
            import ldap
            if self.__authremote['port']:
                port = int(self.__authremote['port'])
            try:
                M = ldap.initialize("ldap://%s:%s" % (self.__authremote['host'],
                                                      self.__authremote['port']))
                M.simple_bind_s(self.__authremote['dn'] % { 'user': username }, password)
                M.unbind_s()
                return 1
            except:
                self.debug( "ldap authentication for %s@%s failed" % \
                      (username, self.__authremote['host']) )
                return 0
        # proto not implemented
        self.debug( "Error: protocol %s not implemented" % \
                self.__authremote['proto'] )
        return 0

    def __pipefd3(self, command, *strings):
        """Executes a command, feeding strings into fd#3
        Returns the errorcode"""
        self.debug( "UID = %d, EUID = %d" % (os.getuid(), os.geteuid()))
        fd3read, fd3write = os.pipe()
        # Attach the pipe to FD 3 if it os not already.
        if fd3read != 3:
            try:
                os.close(3)
                os.dup2(fd3read,3)
            except Exception, err:
                self.debug( "Pipefd3: %s (%s)" % (err.__class__, err) )
                raise err
        self.debug( "Successful pipe()." )
        pid = os.fork()
        if pid == 0:
            # *** Child ***
            # Close other fd's
            os.close(fd3write)
            try:
                # Exec the program
                os.execvp(command.split()[0], command.split())
            except Exception, err:
                self.debug( "Pipefd3: Execvp %s (%s)" % (err.__class__, err) )
                os._exit(200)
        # *** Parent ***
        self.debug( "Successful fork(), PID = %d" % pid )
        # Open pipe into FD3
        os.close(fd3read)
        fd3 = os.fdopen(fd3write, 'w', -1)
        # Feed in the input
        for s in strings:
            fd3.write(s)
        fd3.flush()
        fd3.close()
        # Wait for command to exit
        pid, status = os.waitpid(pid, 0)
        self.debug( "PID = %d, status = %d" % (pid, status))
        # Return the errorcode
        return status

    def __pipecmd(self, command, *strings):
        """Execs a command and pipes strings into stdin
        Returns the errorcode"""
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
        self.__lastcmderr = cmderr.read().strip()
        cmderr.close()
        # Read from the fromchild object.
        self.__lastcmdout = cmdout.read().strip()
        cmdout.close()
        # Get exit status from the wait() member function.
        return cmd.wait()

    def __authfile2dict(self, authfile):
        """Iterate over a tmdauth authentication file, and return a
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

    def __ipfile2dict(self, ipfile):
        """Iterate 'ipauthmapfile' (IP1:IP2:port) and return a dictionary
        containing IP1 -> IP2:port hashes."""
        ipauthmap = {}
        try:
            fp = file(ipfile, 'r')
            for line in fp:
                line = line.strip()
                if line == "":
                    continue
                ipdata = line.split(':', 1)
                ipauthmap[ipdata[0].strip()] = ipdata[1].strip()
            fp.close()
        except IOError:
            pass
        return ipauthmap

    def __update_authdict(self, Force = 0 ):
        """Updates __authdict if __authfile has changed since last update"""
        filemodtime = os.stat( self.__authfile )[8]
        if Force or self.__authdictupdate is None or \
            self.__authdictupdate < filemodtime:
            self.__authdict = self.__authfile2dict( self.__authfile )
            self.__authdictupdate = time.time()

    def __b64_encode(self, s):
        """base64 encoding without the trailing newline."""
        return base64.encodestring(s)[:-1]

    def __b64_decode(self, s):
        """base64 decoding."""
        return base64.decodestring(s)
