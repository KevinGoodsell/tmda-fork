import unittest
import os
import subprocess
import signal
import socket
import re

import OpenSSL.SSL as SSL

class Server(object):
    _port = 8025

    _executable = '../bin/tmda-ofmipd'
    _commonServerArgs = ['-d', '-f', '-p', '127.0.0.1:%d' % _port, '-a',
                         'test-ofmipd.auth']
    _certKeyServerArgs = ['--ssl-cert=test-ofmipd.cert',
                          '--ssl-key=test-ofmipd.key']

    def __init__(self, sslArg=None):
        self._sslArg = sslArg
        self._serverProc = None

    def start(self):
        serverArgs = [self._executable]
        serverArgs.extend(self._commonServerArgs)
        if self._sslArg:
            serverArgs.append(self._sslArg)
            serverArgs.extend(self._certKeyServerArgs)

        newEnv = dict(os.environ)
        newEnv['PYTHONPATH'] = '..'

        self._serverProc = subprocess.Popen(serverArgs, env=newEnv)

        # Wait for server availability
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                s.connect(('127.0.0.1', self.port()))
                s.close()
                break
            except socket.error:
                pass

    def stop(self):
        os.kill(self._serverProc.pid, signal.SIGTERM)
        self._serverProc.wait()

    def port(self):
        return self._port

class Client(object):
    def __init__(self, port):
        self._port = port
        self._address = ('127.0.0.1', port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self._sock.connect(self._address)
        self._sock.recv(200)

    def receiveUntil(self, finished):
        data = ''
        while not finished(data):
            data += self._sock.recv(200)
        return data

    _responseMatcher = re.compile(r'^\d{3} .*\r\n', re.MULTILINE)
    def _completeResponse(self, data):
        return self._responseMatcher.search(data) is not None

    def exchange(self, msg):
        self._sock.send(msg)
        response = self.receiveUntil(self._completeResponse)
        return response

    _responseLineMatcher = re.compile(r'^(?P<code>\d{3})[- ](?P<line>.*)\r\n',
                                      re.MULTILINE)
    def splitResponse(self, response):
        'return (code, [lines])'
        lines = []
        code = None
        for m in self._responseLineMatcher.finditer(response):
            newCode = int(m.group('code'))
            if code is not None and code != newCode:
                raise ValueError('mismatched result codes in response')
            code = newCode
            lines.append(m.group('line'))

        return (code, lines)

class SslClient(Client):
    def __init__(self, port):
        Client.__init__(self, port)
        self._sslSock = None
        self._normalSock = self._sock

    def startSsl(self):
        context = SSL.Context(SSL.SSLv23_METHOD)
        self._sslSock = SSL.Connection(context, self._normalSock)
        self._sslSock.set_connect_state()

        self._sock = self._sslSock

class ServerResposeTestMixin(object):
    def setUp(self):
        self.serverSetUp()
        self.clientSetUp()

        response = self.client.exchange('EHLO test.com\r\n')
        (code, lines) = self.client.splitResponse(response)
        self.ehloCode = code
        self.ehloLines = lines

    def tearDown(self):
        self.server.stop()

    def serverSetUp(self):
        self.server = Server()
        self.server.start()

    def clientSetUp(self):
        self.client = Client(self.server.port())
        self.client.connect()

    def checkExtensions(self, extensions):
        raise NotImplementedError()

    def checkAuthTypes(self, authTypes):
        raise NotImplementedError()

    def testExtensions(self):
        self.failUnless(self.ehloCode == 250)
        extensions = []
        authTypes = []
        for line in self.ehloLines[1:]:
            if line.startswith('AUTH '):
                authTypes.extend(line.split()[1:])

            parts = line.split(' ', 1)
            extensions.append(parts[0])

        self.checkExtensions(extensions)
        self.checkAuthTypes(authTypes)

class UnencryptedServerResponses(ServerResposeTestMixin, unittest.TestCase):
    def checkExtensions(self, extensions):
        self.failUnless(extensions == ['AUTH'])

    def checkAuthTypes(self, authTypes):
        self.failUnless(set(authTypes) == set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

class SslServerResponses(ServerResposeTestMixin, unittest.TestCase):
    def serverSetUp(self):
        self.server = Server('--ssl')
        self.server.start()

    def clientSetUp(self):
        self.client = SslClient(self.server.port())
        self.client.startSsl()
        self.client.connect()

    def checkExtensions(self, extensions):
        self.failUnless(extensions == ['AUTH'])

    def checkAuthTypes(self, authTypes):
        self.failUnless(set(authTypes) == set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

class PreStartTlsServerResponses(ServerResposeTestMixin, unittest.TestCase):
    def serverSetUp(self):
        self.server = Server('--tls=on')
        self.server.start()

    def clientSetUp(self):
        self.client = SslClient(self.server.port())
        self.client.connect()

    def checkExtensions(self, extensions):
        self.failUnless(extensions == ['STARTTLS'])

    def checkAuthTypes(self, authTypes):
        self.failUnless(len(authTypes) == 0)

class PostStartTlsServerResponses(ServerResposeTestMixin, unittest.TestCase):
    def serverSetUp(self):
        self.server = Server('--tls=on')
        self.server.start()

    def clientSetUp(self):
        self.client = SslClient(self.server.port())
        self.client.connect()
        response = self.client.exchange('STARTTLS\r\n')
        (code, lines) = self.client.splitResponse(response)
        assert(code == 220)
        self.client.startSsl()

    def checkExtensions(self, extensions):
        self.failUnless(extensions == ['AUTH'])

    def checkAuthTypes(self, authTypes):
        self.failUnless(set(authTypes) == set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

class OptionalStartTlsServerResponses(ServerResposeTestMixin,
                                      unittest.TestCase):
    def serverSetUp(self):
        self.server = Server('--tls=optional')
        self.server.start()

    def checkExtensions(self, extensions):
        self.failUnless(set(extensions) == set(['STARTTLS', 'AUTH']))

    def checkAuthTypes(self, authTypes):
        self.failUnless(set(authTypes) == set(['LOGIN', 'PLAIN', 'CRAM-MD5']))

# XXX Add tests:
# Send message success and failure
# Authenticate success and failure for each method

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
