import unittest
import hmac
import sys
from hashlib import md5
import os

import lib.util
lib.util.testPrep()
from lib.ofmipd import TestOfmipdServer, ServerClientMixin

verbose = False

class FileAuthServerClientMixin(ServerClientMixin):
    def serverAddOptions(self):
        self.server.addFileAuth()
        self.server.debug(verbose)

class ServerResponseTestMixin(FileAuthServerClientMixin):
    def clientBeginCommunication(self):
        (code, lines) = self.client.exchange('EHLO test.com\r\n')
        self.ehloCode = code
        self.ehloLines = lines

    def checkExtensions(self, extensions):
        raise NotImplementedError()

    def checkAuthTypes(self, authTypes):
        raise NotImplementedError()

    def testExtensions(self):
        self.assertEqual(self.ehloCode, 250)
        extensions = []
        authTypes = []
        for line in self.ehloLines[1:]:
            if line.startswith('AUTH '):
                authTypes.extend(line.split()[1:])

            parts = line.split(' ', 1)
            extensions.append(parts[0])

        self.checkExtensions(extensions)
        self.checkAuthTypes(authTypes)

    def testStartTls(self):
        (code, lines) = self.client.exchange('STARTTLS\r\n')
        self.assertEqual(code, self.expectedStartTlsCode)

    def testAuth(self):
        (code, lines) = self.client.exchange('AUTH LOGIN\r\n')
        self.assertEqual(code, self.expectedAuthCode)

class UnencryptedServerResponses(ServerResponseTestMixin, unittest.TestCase):
    expectedStartTlsCode = 502
    expectedAuthCode = 334

    def checkExtensions(self, extensions):
        self.assertEqual(extensions, ['AUTH'])

    def checkAuthTypes(self, authTypes):
        self.assertEqual(set(authTypes), set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

class SslServerResponses(ServerResponseTestMixin, unittest.TestCase):
    expectedStartTlsCode = 503
    expectedAuthCode = 334

    def serverAddOptions(self):
        ServerResponseTestMixin.serverAddOptions(self)
        self.server.ssl()

    def checkExtensions(self, extensions):
        self.assertEqual(extensions, ['AUTH'])

    def checkAuthTypes(self, authTypes):
        self.assertEqual(set(authTypes), set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

class PreStartTlsServerResponses(ServerResponseTestMixin, unittest.TestCase):
    expectedStartTlsCode = 220
    expectedAuthCode = 530
    client_starttls_on_connect = False

    def serverAddOptions(self):
        ServerResponseTestMixin.serverAddOptions(self)
        self.server.tls('on')

    def checkExtensions(self, extensions):
        self.assertEqual(extensions, ['STARTTLS'])

    def checkAuthTypes(self, authTypes):
        self.assertEqual(len(authTypes), 0)

class PostStartTlsServerResponses(ServerResponseTestMixin, unittest.TestCase):
    expectedStartTlsCode = 503
    expectedAuthCode = 334

    def serverAddOptions(self):
        ServerResponseTestMixin.serverAddOptions(self)
        self.server.tls('on')

    def checkExtensions(self, extensions):
        self.assertEqual(extensions, ['AUTH'])

    def checkAuthTypes(self, authTypes):
        self.assertEqual(set(authTypes), set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

class OptionalStartTlsServerResponses(ServerResponseTestMixin,
                                      unittest.TestCase):
    expectedStartTlsCode = 220
    expectedAuthCode = 334
    client_starttls_on_connect = False

    def serverAddOptions(self):
        ServerResponseTestMixin.serverAddOptions(self)
        self.server.tls('optional')

    def checkExtensions(self, extensions):
        self.assertEqual(set(extensions), set(['STARTTLS', 'AUTH']))

    def checkAuthTypes(self, authTypes):
        self.assertEqual(set(authTypes), set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

# These authentication tests differ from the tests in test-ofmipd-auth.py file
# in that these test authentication between an SMTP client and the tmda-ofmipd
# server. test-ofmipd-auth.py tests tmda-ofmipd's backend authentication
# methods, such as authenticating against a password file or a different server.
class AuthenticationTests(FileAuthServerClientMixin, unittest.TestCase):
    def authPlain(self, username, password, expectedCode):
        authString = '\x00'.join([username, username, password])
        authString = authString.encode('base64')[:-1]
        (code, lines) = self.client.exchange('AUTH PLAIN %s\r\n' % authString)

        self.assertEqual(code, expectedCode,
            'username: %r password: %r code: %d' % (username, password, code))

    def authLogin(self, username, password, firstCode, secondCode):
        userString = username.encode('base64')[:-1]
        passString = password.encode('base64')[:-1]

        userPrompt = 'Username:'.encode('base64')[:-1]
        passPrompt = 'Password:'.encode('base64')[:-1]

        (code, lines) = self.client.exchange('AUTH LOGIN\r\n')
        self.assertEqual(code, 334)
        self.assertEqual(lines[0], userPrompt)

        (code, lines) = self.client.exchange(userString + '\r\n')
        self.assertEqual(code, firstCode)

        if firstCode == 334:
            self.assertEqual(lines[0], passPrompt)

            (code, lines) = self.client.exchange(passString + '\r\n')
            self.assertEqual(code, secondCode,
                'username: %r password: %r code: %d' % \
                (username, password, code))

    def authCramMd5(self, username, password, expectedCode):
        (code, lines) = self.client.exchange('AUTH CRAM-MD5\r\n')
        self.assertEqual(code, 334)
        self.assertEqual(len(lines), 1)

        ticket = lines[0].decode('base64')
        digest = hmac.new(password, ticket, md5).hexdigest()
        message = '%s %s' % (username, digest)
        message = message.encode('base64')[:-1]

        (code, lines) = self.client.exchange('%s\r\n' % message)
        self.assertEqual(code, expectedCode,
            'username: %r password: %r code: %d' % (username, password, code))

    def testPlain(self):
        self.authPlain('testuser', 'testpassword', 235)

    def testLogin(self):
        self.authLogin('testuser', 'testpassword', 334, 235)

    def testCramMd5(self):
        self.authCramMd5('testuser', 'testpassword', 235)

    def testPlainFailure(self):
        for (username, password) in lib.util.badUsersPasswords('testuser',
                                                               'testpassword'):
            self.authPlain(username, password, 535)

    def testLoginFailure(self):
        for (username, password) in lib.util.badUsersPasswords('testuser',
                                                               'testpassword'):
            self.authLogin(username, password, 334, 535)

    def testCramMd5Failure(self):
        for (username, password) in lib.util.badUsersPasswords('testuser',
                                                               'testpassword'):
            self.authCramMd5(username, password, 535)

# Provides functions for sending mail
class SendMailMixin(FileAuthServerClientMixin):
    def beginSend(self):
        (code, lines) = self.client.exchange('MAIL FROM: testuser@nowhere.com'
                                             '\r\n')
        self.assertEqual(code, 250)

        (code, lines) = self.client.exchange('RCPT TO: fakeuser@fake.com\r\n')
        self.assertEqual(code, 250)

        (code, lines) = self.client.exchange('DATA \r\n')
        self.assertEqual(code, 354)

    def sendLine(self, line):
        self.client.send('%s\r\n' % line)

    def finishSend(self, expectedCode=250):
        (code, lines) = self.client.exchange('.\r\n')
        self.assertEqual(code, expectedCode)

# Tests for sending mail

class SendTestMixin(SendMailMixin):
    def testSend(self):
        self.client.signOn()
        self.beginSend()
        self.sendLine('X-nothing: nothing')
        self.sendLine('')
        self.sendLine('Shut up.')
        self.finishSend()

    def testSendFailure(self):
        (code, lines) = self.client.exchange('MAIL TO: testuser@nowhere.com'
                                             '\r\n')
        self.assertEqual(code, 530)

class SslSendTestMixin(SendTestMixin):
    def serverAddOptions(self):
        SendTestMixin.serverAddOptions(self)
        self.server.ssl()

class TlsSendTestMixin(SendTestMixin):
    def serverAddOptions(self):
        SendTestMixin.serverAddOptions(self)
        self.server.tls('on')

# End of mixins, start actual tests constructed from mixins. Starting with
# default IPv6 tests, followed by IPv4 variants:

class UnencryptedSendTest(SendTestMixin, unittest.TestCase):
    pass

class SslSendTest(SslSendTestMixin, unittest.TestCase):
    pass

class TlsSendTest(TlsSendTestMixin, unittest.TestCase):
    pass

# IPv4 variants:

class UnencryptedSendV4Test(SendTestMixin, unittest.TestCase):
    client_addr = 'v4' # Any available IPv4 address

class SslSendV4Test(SslSendTestMixin, unittest.TestCase):
    client_addr = 'v4'

class TlsSendV4Test(TlsSendTestMixin, unittest.TestCase):
    client_addr = 'v4'


class QuotaTest(SendMailMixin, unittest.TestCase):
    def serverAddOptions(self):
        SendMailMixin.serverAddOptions(self)
        self.server.addOptions(['--throttle-script', 'bin/throttle'])

    def sendMessage(self, username, password, expectedCode):
        self.client.signOn(username, password)
        self.beginSend()
        self.sendLine('X-Test: Quota')
        self.sendLine('')
        self.sendLine('Short message.')
        self.finishSend(expectedCode)

        # Bug: Server sends 250 immediately after 450 (over quota)
        (code, lines) = self.client.exchange('Nonsense\r\n')
        self.assertEqual(code, 502)

    def testUnderQuota(self):
        self.sendMessage('testuser', 'testpassword', 250)

    def testOverQuota(self):
        self.sendMessage('overquota', 'quotapassword', 450)

# Test for the undocumented ipauthmap file.
class IpAuthMapTest(unittest.TestCase):
    def setUp(self):
        self.importOfmipd()

    def importOfmipd(self):
        # Cheap way of "importing" a script.
        self.module = {}
        ofmipd = os.path.join(lib.util.rootDir, 'bin', 'tmda-ofmipd')
        execfile(ofmipd, self.module)

    def testAuthMapRead(self):
        RemoteAuthenticator = self.module['RemoteAuthenticator']
        test_file = os.path.join('files', 'test-ipauthmap')
        mapping = RemoteAuthenticator._addrdict(test_file)

        # Most of the tests are handled in checkMapping, and include a variant
        # with port and without.
        self.checkMapping(mapping, with_port=True)
        self.checkMapping(mapping, with_port=False)

        # These tests have spacing variations in the test file.
        self.assertEqual(mapping['127.2.1.1'], ('192.168.1.1', 1001))
        self.assertEqual(mapping['127.2.1.2'], ('192.168.1.2', 1002))
        self.assertEqual(mapping['127.2.1.3'], ('192.168.1.3', 1003))
        self.assertEqual(mapping['127.2.1.4'], ('192.168.1.4', 1004))

    def checkMapping(self, mapping, with_port):
        if with_port:
            ip4pre = '127.0.'
            ip6pre = '7F00:'
            port = lambda p: p
        else:
            ip4pre = '127.1.'
            ip6pre = '7F01:'
            port = lambda p: None

        # These follow the layout of the test file.
        val = mapping[ip4pre + '0.1']
        self.assertEqual(val, ('192.168.0.1', port(1001)))
        val = mapping[ip4pre + '0.2']
        self.assertEqual(val, ('192.168.0.2', port(1002)))

        val = mapping[ip4pre + '1.1']
        self.assertEqual(val, ('192.168.1.1', port(1001)))
        val = mapping[ip4pre + '1.2']
        self.assertEqual(val, ('192.168.1.2', port(1002)))

        val = mapping[ip4pre + '2.1']
        self.assertEqual(val, ('::ffff:192.168.2.1', port(1001)))
        val = mapping[ip4pre + '2.2']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:ffff:192.168.2.2',
                               port(1002)))
        val = mapping[ip4pre + '2.3']
        self.assertEqual(val, ('0:0:0:0:0:ffff:192.168.2.3', port(1003)))

        val = mapping[ip4pre + '3.1']
        self.assertEqual(val, ('::1', port(1001)))
        val = mapping[ip4pre + '3.2']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:0000:0000:0002',
                               port(1002)))
        val = mapping[ip4pre + '3.3']
        self.assertEqual(val, ('0:0:0:0:0:0:0:3', port(1003)))

        pre = '0000:0000:0000:0000:0000:FFFF:' + ip6pre

        val = mapping[pre + '0401']
        self.assertEqual(val, ('192.168.4.1', port(1001)))

        val = mapping[pre + '0501']
        self.assertEqual(val, ('::ffff:192.168.5.1', port(1001)))
        val = mapping[pre + '0502']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:ffff:192.168.5.2',
                               port(1002)))
        val = mapping[pre + '0503']
        self.assertEqual(val, ('0:0:0:0:0:ffff:192.168.5.3', port(1003)))

        val = mapping[pre + '0601']
        self.assertEqual(val, ('::1', port(1001)))
        val = mapping[pre + '0602']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:0000:0000:0002',
                               port(1002)))
        val = mapping[pre + '0603']
        self.assertEqual(val, ('0:0:0:0:0:0:0:3', port(1003)))

        pre = '0:0:0:0:0:FFFF:' + ip6pre

        val = mapping[pre + '0701']
        self.assertEqual(val, ('192.168.7.1', port(1001)))

        val = mapping[pre + '0801']
        self.assertEqual(val, ('::ffff:192.168.8.1', port(1001)))
        val = mapping[pre + '0802']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:ffff:192.168.8.2',
                               port(1002)))
        val = mapping[pre + '0803']
        self.assertEqual(val, ('0:0:0:0:0:ffff:192.168.8.3', port(1003)))

        val = mapping[pre + '0901']
        self.assertEqual(val, ('::1', port(1001)))
        val = mapping[pre + '0902']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:0000:0000:0002',
                               port(1002)))
        val = mapping[pre + '0903']
        self.assertEqual(val, ('0:0:0:0:0:0:0:3', port(1003)))

        pre = '::FFFF:' + ip6pre

        val = mapping[pre + '0a01']
        self.assertEqual(val, ('192.168.10.1', port(1001)))

        val = mapping[pre + '0b01']
        self.assertEqual(val, ('::ffff:192.168.11.1', port(1001)))
        val = mapping[pre + '0b02']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:ffff:192.168.11.2',
                               port(1002)))
        val = mapping[pre + '0b03']
        self.assertEqual(val, ('0:0:0:0:0:ffff:192.168.11.3', port(1003)))

        val = mapping[pre + '0c01']
        self.assertEqual(val, ('::1', port(1001)))
        val = mapping[pre + '0c02']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:0000:0000:0002',
                               port(1002)))
        val = mapping[pre + '0c03']
        self.assertEqual(val, ('0:0:0:0:0:0:0:3', port(1003)))

        pre = '::FFFF:' + ip4pre

        val = mapping[pre + '13.1']
        self.assertEqual(val, ('192.168.13.1', port(1001)))

        val = mapping[pre + '14.1']
        self.assertEqual(val, ('::ffff:192.168.14.1', port(1001)))
        val = mapping[pre + '14.2']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:ffff:192.168.14.2',
                               port(1002)))
        val = mapping[pre + '14.3']
        self.assertEqual(val, ('0:0:0:0:0:ffff:192.168.14.3', port(1003)))

        val = mapping[pre + '15.1']
        self.assertEqual(val, ('::1', port(1001)))
        val = mapping[pre + '15.2']
        self.assertEqual(val, ('0000:0000:0000:0000:0000:0000:0000:0002',
                               port(1002)))
        val = mapping[pre + '15.3']
        self.assertEqual(val, ('0:0:0:0:0:0:0:3', port(1003)))

# XXX Add tests:
# Dupes and syntax errors

if __name__ == '__main__':
    if '-v' in sys.argv:
        verbose = True
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
