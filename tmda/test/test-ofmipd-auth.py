import unittest
import sys

import lib.util
lib.util.testPrep()
from lib.ofmipd import TestOfmipdServer, ServerClientMixin

verbose = False

# These tests are hugely problematic because they depend heavily on the
# environment in which they are being run. The tests may have to be edited
# by hand to fit the test environment (e.g., setting usernames and passwords).
# Each test has notes on getting it to work.
#
# As a general note, it may be useful to install and run servers, and create
# test accounts, in a chrooted installation. I used debootstrap to create a
# fresh Debian installation in which I created user testuser and installed
# dovecot, OpenLDAP, etc.
#
# Note that you can run this with a -v argument to get all the debug output from
# tmda-ofmipd.

class AuthMixin(ServerClientMixin):
    # Replace these in test classes if necessary.
    username = 'testuser'
    password = 'testpassword'

    # Print messages for non-verbose mode only
    @classmethod
    def quiet(cls, msg, *args):
        if not verbose:
            print msg % args

    def serverAddOptions(self):
        self.addAuth()
        self.server.debug(verbose)

    def addAuth(self):
        raise NotImplementedError()

class RemoteAuthMixin(AuthMixin):
    # Derived classes must provide 'protocol', and may provide an alternate
    # port and/or path.
    protocol = None
    port = None
    path = ''
    host = 'localhost'

    def addAuth(self):
        portStr = ''
        if self.port is not None:
            portStr = ':%d' % self.port

        self.server.addRemoteAuth('%s://%s%s/%s' % (self.protocol, self.host,
                                                    portStr, self.path))

class AuthTestMixin(object):
    def testAuthentication(self):
        try:
            self.client.signOn(self.username, self.password)
        except StandardError, e:
            self.fail(str(e))

    def testAuthenticationFailure(self):
        # There's some extra logging here for non-verbose mode because
        # this test can take a while and may appear frozen. In verbose
        # mode it's totally unnecessary and mostly useless because it
        # there's so much other noise.
        self.quiet("\nTesting 'username':'password':")
        for (username, password) in lib.util.badUsersPasswords(self.username,
                                                               self.password):
            self.quiet('  %r:%r', username, password)
            self.assertRaises(AssertionError, self.client.signOn,
                              username, password)

# For convenience, local and remote auth test mixins
class LocalAuthTestMixin(AuthMixin, AuthTestMixin):
    pass

class RemoteAuthTestMixin(RemoteAuthMixin, AuthTestMixin):
    pass

# AuthFileTest and AuthProgTest should run with no problems. Unlike the
# rest of the tests, everything they need is provided right in the test
# directory.
class AuthFileTest(LocalAuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addFileAuth()

class AuthProgTest(LocalAuthTestMixin, unittest.TestCase):
    username = 'authproguser'
    password = 'abracadabra'

    def addAuth(self):
        self.server.addProgAuth('bin/checkpassword.py')

# (These notes may be Linux-specific)
# In general, testuser needs to exist as a real system user (possibly in a
# chrooted system) for the PAM tests to work. In addition, the user running the
# test has to have read access to the system password hashes. Typically the
# password hashes are in a read-protected file called /etc/shadow.
#
# One approach to getting access is to add the user to the 'shadow' group. This
# works on systems where the shadow file's group is 'shadow' and it has group
# read permissions.
#
# Another approach is to "unshadow" the passwords. The command 'pwunconv' can be
# used to remove the shadow file and put the hashes in the /etc/passwd file,
# which is readable by all users.
class AuthPamTest(LocalAuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addPamAuth('login')

# For AuthImapTest, AuthImapsTest, AuthPop3Test, and AuthApopTest, Dovecot may
# be used as an authentication server. Under Debian, with the dovecot-imapd and
# dovecot-pop3d packages, try the following configuration changes.
#
# # dovecot.conf:
# listen = 127.0.0.1, ::1
# # For getting around failure delays:
# login_trusted_networks = 127.0.0.0/24, ::1/128
#
# # conf.d/10-auth.conf:
# auth_failure_delay = 0 secs
# auth_mechanisms = plain apop
# # Remove any !include auth-* lines and use this instead:
# userdb {
#   driver = passwd
# }
# passdb {
#   driver = passwd-file
#   args = /etc/dovecot/passwd
# }
#
# # conf.d/10-mail.conf:
# mail_location = maildir:~/Maildir
#
# For apop the server needs to have the plain-text password, so create
# /etc/dovecot/passwd with this content:
#
# testuser:{PLAIN}testpassword::::::nodelay=y
class AuthImapTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'imap'

# Repeat of the last test with IPv6
class AuthImapV6Test(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'imap'
    host = '[::1]'

class AuthImapsTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'imaps'

class AuthPop3Test(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'pop3'

class AuthApopTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'apop'

# OpenLDAP can be used for AuthLdapTest. The relevant Debian packages
# are ldap-utils (which includes ldapadd) and slapd, the OpenLDAP
# daemon.
#
# During installation of slapd, an administrator password is required. This is
# used in the ldapadd command later.
#
# To add the user to the LDAP database put the following in a file named
# test.ldif:
#
# dn: ou=people,dc=nodomain
# objectclass: organizationalUnit
# ou: people
#
# dn: uid=testuser,ou=people,dc=nodomain
# sn: User
# cn: Test User
# objectclass: top
# objectclass: person
# objectclass: organizationalPerson
# objectclass: inetOrgPerson
# ou: People
# uid: testuser
# userpassword: testpassword
#
# And install it with this:
#
# ldapadd -x -h localhost -D cn=admin,dc=nodomain -w password -f test.ldif
class AuthLdapTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'ldap'
    path = 'uid=%s,ou=people,dc=nodomain'

# Notes for the AuthImapTest and AuthProgTest apply to Chain tests.
class AuthChainTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'imap'

    def addAuth(self):
        self.server.addProgAuth('bin/checkpassword.py')
        RemoteAuthTestMixin.addAuth(self)

# Same as AuthChainTest, just making sure it has to check the other item in the
# authentication chain by using a different user.
class AuthChainAltTest(AuthChainTest):
    username = 'authproguser'
    password = 'abracadabra'

# Tests for failed connections to remote authenticators

class RemoteAuthMissingMixin(RemoteAuthMixin):
    # No authenticators should be listening on this address
    host = '127.0.0.2'

    def testFailedConnection(self):
        try:
            self.client.signOn(self.username, self.password)
            self.fail('Logging in succeeded with an invalid authenticator')
        except StandardError, e:
            pass

class RemoteAuthMissingImapTest(RemoteAuthMissingMixin, unittest.TestCase):
    protocol = 'imap'

class RemoteAuthMissingImapsTest(RemoteAuthMissingMixin, unittest.TestCase):
    protocol = 'imaps'

class RemoteAuthMissingPop3Test(RemoteAuthMissingMixin, unittest.TestCase):
    protocol = 'pop3'

class RemoteAuthMissingApopTest(RemoteAuthMissingMixin, unittest.TestCase):
    protocol = 'apop'

class RemoteAuthMissingLdapTest(RemoteAuthMissingMixin, unittest.TestCase):
    protocol = 'ldap'
    path = 'uid=%s,ou=people,dc=nodomain'

# Tests for ipauthmap file

class AuthMapMixin(RemoteAuthMixin):
    protocol = 'imap'
    host = '0.0.0.0'

    def serverCreate(self):
        # Need to listen on many address to test connecting on different
        # addresses that may map to other addresses.
        return TestOfmipdServer(['::1', '127.0.0.2', '127.0.0.3', '127.0.0.4',
                                 '127.0.0.5'])

    def testMappingAuth(self):
        try:
            self.client.signOn(self.username, self.password)
        except StandardError, e:
            self.fail(str(e))

class AuthMapV4ToV4Test(AuthMapMixin, unittest.TestCase):
    client_addr = ('127.0.0.2', 8025)

class AuthMapV4ToV6Test(AuthMapMixin, unittest.TestCase):
    client_addr = ('127.0.0.3', 8025)

class AuthMapV6ToV4Test(AuthMapMixin, unittest.TestCase):
    client_addr = ('::1', 8025)

class AuthMapFallbackTest(AuthMapMixin, unittest.TestCase):
    # Address that isn't in the ipauthmapfile
    client_addr = ('127.0.0.5', 8025)

class AuthMapFailureTest(AuthMapMixin, unittest.TestCase):
    # Address that maps to an address that nothing is listening on
    client_addr = ('127.0.0.4', 8025)

    def testMappingAuth(self):
        try:
            self.client.signOn(self.username, self.password)
            self.fail('Logging in succeeded with an invalid authenticator '
                      'mapping')
        except StandardError, e:
            pass

if __name__ == '__main__':
    if '-v' in sys.argv:
        verbose = True
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
