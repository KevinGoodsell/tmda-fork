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

# AuthFileTest and AuthProgTest should run with no problems. Unlike the
# rest of the tests, everything they need is provided right in the test
# directory.
class AuthFileTest(AuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addFileAuth()

class AuthProgTest(AuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addProgAuth('bin/checkpassword.py')

# (These notes may be Linux-specific)
# This only works if the test is run as the user being authenticated, root,
# or (if supported) a member of the shadow group.
#
# A custom PAM service could possibly work around this, but the way I did it
# is to run the test as testuser, after creating that user in a chroot jail.
class AuthPamTest(AuthTestMixin, unittest.TestCase):
    def addAuth(self):
        self.server.addPamAuth('login')

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

# OpenLDAP works for this... sort of. Configuring is problematic, and needs
# more documentation here.
#
# Here are basic instructions for adding the LDAP user. Stick this in
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
# ldapadd -x -h localhost -D cn=admin,dc=nodomain -w password -f test.ldif
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
