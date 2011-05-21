import unittest
import sys
import urlparse

import lib.util
lib.util.testPrep()

import TMDA.Util as Util

# Refer to RFC 3986 for URL format details.
class UrlSplit(unittest.TestCase):
    def testNonV6(self):
        urls = [
            'http://foo.com/path',
            'http://foo.com:33/path?query#fragment',
            'ftp://111.222.0.1/path',
            'ftp://111.222.0.1:99/path?query#fragment',
        ]

        for url in urls:
            result = Util.urlsplit(url)
            self.assertTrue(isinstance(result, urlparse.SplitResult))

    def testV6(self):
        tests = [
            (
                # First test shows all the parts for reference
                'http://user:pass@[::1]:33/path?query#fragment',
                ('http', 'user:pass@[::1]:33', '/path', 'query', 'fragment',
                 'user', 'pass', '::1', 33)
            ),
            (
                '//[::1]',
                ('', '[::1]', '', '', '', None, None, '::1', None)
            ),
            (
                # Case-insensitivity
                'ftp://[dead:BEEF:1234:5678:aA09::1]',
                ('ftp', '[dead:BEEF:1234:5678:aA09::1]', '', '', '', None, None,
                 'dead:BEEF:1234:5678:aA09::1', None)
            ),
            (
                'http://user:pass@[0000:0000:0000:0000:0000:0000:0000:0001]:33/path',
                ('http',
                 'user:pass@[0000:0000:0000:0000:0000:0000:0000:0001]:33',
                 '/path', '', '', 'user', 'pass',
                 '0000:0000:0000:0000:0000:0000:0000:0001', 33)
            ),
            (
                'http://[::ffff:127.0.0.1]/',
                ('http', '[::ffff:127.0.0.1]', '/', '', '', None, None,
                 '::ffff:127.0.0.1', None)
            ),
            (
                'http://user:pass@[0000:0000:0000:0000:0000:ffff:127.0.0.1]:33/path?query#fragment',
                ('http',
                 'user:pass@[0000:0000:0000:0000:0000:ffff:127.0.0.1]:33',
                 '/path', 'query', 'fragment', 'user', 'pass',
                 '0000:0000:0000:0000:0000:ffff:127.0.0.1', 33)
            ),
        ]

        print
        for (url, expected) in tests:
            print 'Testing url', url
            result = Util.urlsplit(url)
            self.checkSplitUrl(result, expected)

    def checkSplitUrl(self, result, expected):
        self.assertEqual(tuple(result), expected[:5])
        self.assertEqual(result.username, expected[5])
        self.assertEqual(result.password, expected[6])
        self.assertEqual(result.hostname, expected[7])
        self.assertEqual(result.port, expected[8])


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
