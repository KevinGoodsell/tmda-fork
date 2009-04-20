import unittest

import lib.util
from lib.ofmipd import TestOfmipdServer

# These tests are hugely problematic because they depend heavily on the
# environment in which the are being run. The tests may have to be editted
# by hand to fit the test environment (e.g., setting usernames and passwords).
# Each test has notes on getting it to work.
#
# As a general note, it may be useful to install and run servers, and create
# test accounts, in a chrooted installation. I used debootstrap to create a
# fresh Debian installation in which I created user testuser and installed
# dovecot, OpenLDAP, etc.

class AuthTestMixin(object):
    # Replace these in test classes if necessary.
    username = 'testuser'
    password = 'testpassword'

    badUsers = ['ttestuser', 'teestuser', 'testuserr', 'tsstuser', 'testuse']
    badPasswords = ['', 'ttestpassword', 'testpasswordd', 'tsstpassword',
                    'testpasswor']

    def setUp(self):
        self.serverSetUp()
        self.clientSetUp()

    def tearDown(self):
        self.server.stop()

    def serverSetUp(self):
        self.server = TestOfmipdServer()
        self.addAuth()
        self.server.debug()
        self.server.start()

    def addAuth(self):
        raise NotImplementedError()

    def clientSetUp(self):
        self.client = self.server.makeClient()
        self.client.connect(start_tls=True)

    def testAuthentication(self):
        try:
            self.client.signOn(self.username, self.password)
        except StandardError, e:
            self.fail(str(e))

    def testAuthenticationFailure(self):
        for username in self.badUsers:
            self.assertRaises(AssertionError, self.client.signOn,
                              username, self.password)

        for password in self.badPasswords:
            self.assertRaises(AssertionError, self.client.signOn,
                              self.username, password)

# This is the one test that should run with no problems.
class AuthFileTest(AuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addFileAuth()

# (These notes may be Linux-specific)
# This only works if the test is run as the user being authenticated (or as
# root). This is basically because the common authentication setup is
# to use the pam_unix module. This module authenticates based on passwd and
# shadow, so would only work for root. To get around this, the module also
# uses a separate suid program, unix_chkpwd, which is very basic and only
# authenticates the current user.
#
# A custom PAM service could possibly work around this, but the way I did it
# is to run the test as testuser, after creating that user in a chroot jail.
class AuthPamTest(AuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addPamAuth('login')

# This test has never been successfully run because I can't find a
# checkpassword program that works.
class AuthProgTest(AuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addProgAuth('/bin/checkpassword /bin/true')

class RemoteAuthTestMixin(AuthTestMixin):
    # Derived classes must provide 'protocol', and may provide an alternate
    # port and/or path.
    protocol = None
    port = None
    path = ''

    def addAuth(self):
        portStr = ''
        if self.port is not None:
            portStr = ':%d' % self.port

        self.server.addRemoteAuth('%s://localhost%s/%s' %
                                  (self.protocol, portStr, self.path))

# For AuthImapTest, AuthImapsTest, and AuthPop3Test, dovecot worked perfectly
# as an authentication server. Under Debian, with the dovecot-imapd and
# dovecot-pop3d packages, the configuration was quite easy. Just make sure
# the 'protocols' setting is 'imap imaps pop3', ssl is enabled (with cert and
# key files), and the user and password databases are set to something sane
# (but consider using passwd-file, see the notes for AuthApopTest).
class AuthImapTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'imap'

class AuthImapsTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'imaps'

class AuthPop3Test(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'pop3'

# AuthApopTest also works well with dovecot, but requires additional
# configuration. apop has to be enabled as an authentication mechanism and
# since apop requires the server to have access to the plaintext password (I
# think), the passdb needs to provide this. Using a passwd-file passdb is an
# easy way to provide this. Just put something like
# 'testuser:{PLAIN}testpassword' in the file.
class AuthApopTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'apop'

# OpenLDAP works for this... sort of. I haven't figured out how to make the
# configuration easy yet. Maybe I'll stick a ldif file here that contains
# the right directory info, and instructions for installing it.
class AuthLdapTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'ldap'
    path = 'uid=%s,ou=people,dc=nodomain'

# Notes for the AuthImapTest and AuthFileTest apply here.
class AuthChainTest(RemoteAuthTestMixin, unittest.TestCase):
    protocol = 'imap'

    def addAuth(self):
        self.server.addFileAuth()
        RemoteAuthTestMixin.addAuth(self)

if __name__ == '__main__':
    lib.util.fixupFiles()

    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
