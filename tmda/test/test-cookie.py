import unittest
import sys

import lib.util
lib.util.testPrep()

import TMDA.Cookie as Cookie

class Cookies(unittest.TestCase):
    time = 1262937386
    pid = 12345
    sender_address = 'Sender@REmote.com'
    user_address = 'testuser@testsite.com'

    keyword_cookies = [
        ('keywordtest', 'keywordtest.243548'),
        ('keyword-test', 'keyword?test.0de87a'),
        # This test doesn't work because make_keyword_address lower-cases the
        # keyword.
        #('KeyWordTest0123', 'KeyWordTest0123.51993d'),
        # All non-alphanumeric characters that should not be replaced
        # with ?
        ("!#$%&*+/=^_`{|}'~", "!#$%&*+/=^_`{|}'~.269c47"),
        # Some characters that should be replaced with ?
        (' "():;<>?@[\\]', '?????????????.372018'),
        # Characters TMDA 1.1.12 gets wrong due to a bad regex in
        # make_keyword_cookie.
        ('.,', '??.925dcc'),
    ]

    def testConfirmCookie(self):
        calculated = Cookie.make_confirm_cookie(self.time, self.pid)
        self.assertEqual(calculated, '1262937386.12345.a45167')

        calculated = Cookie.make_confirm_cookie(self.time, self.pid, 'keyword')
        self.assertEqual(calculated, '1262937386.12345.f5ee35')

    def testConfirmAddress(self):
        calculated = Cookie.make_confirm_address(self.user_address, self.time,
                                                 self.pid)
        self.assertEqual(calculated,
            'testuser-confirm-1262937386.12345.a45167@testsite.com')

        calculated = Cookie.make_confirm_address(self.user_address, self.time,
                                                 self.pid, 'keyword')
        self.assertEqual(calculated,
            'testuser-confirm-1262937386.12345.f5ee35@testsite.com')

    def testDatedCookie(self):
        calculated = Cookie.make_dated_cookie(self.time)
        self.assertEqual(calculated, '1263369386.df2137')

        calculated = Cookie.make_dated_cookie(self.time, '1m')
        self.assertEqual(calculated, '1262937446.926a58')

    def testDatedAddress(self):
        calculated = Cookie.make_dated_address(self.user_address, self.time)
        self.assertEqual(calculated,
            'testuser-dated-1263369386.df2137@testsite.com')

        # "Now" address. Can't predict exactly how it will come out,
        # but make sure it at least succeeds.
        import re
        pattern = re.compile(r'testuser-dated-\d{10}\.[0-9a-f]{6}@testsite\.com')
        calculated = Cookie.make_dated_address(self.user_address)
        self.assertTrue(pattern.match(calculated))

    def testSenderCookie(self):
        calculated = Cookie.make_sender_cookie(self.sender_address.lower())
        self.assertEqual(calculated, '23834d')

        calculated = Cookie.make_sender_cookie(self.sender_address)
        self.assertEqual(calculated, '23834d')

    def testSenderAddress(self):
        calculated = Cookie.make_sender_address(self.user_address,
                                                self.sender_address.lower())
        self.assertEqual(calculated, 'testuser-sender-23834d@testsite.com')

        calculated = Cookie.make_sender_address(self.user_address,
                                                self.sender_address)
        self.assertEqual(calculated, 'testuser-sender-23834d@testsite.com')

    def testKeywordCookie(self):
        for (keyword, cookie) in self.keyword_cookies:
            calculated = Cookie.make_keyword_cookie(keyword)
            self.assertEqual(calculated, cookie)

        # With uppercase characters (not allowed in keyword addresses).
        self.assertEqual(
            Cookie.make_keyword_cookie('KeyWordTest0123'),
            'KeyWordTest0123.51993d'
        )

    def testKeywordAddress(self):
        for (keyword, cookie) in self.keyword_cookies:
            calculated = Cookie.make_keyword_address(self.user_address,
                                                     keyword)
            expected = 'testuser-keyword-%s@testsite.com' % cookie
            self.assertEqual(calculated, expected)

class Fingerprints(unittest.TestCase):
    def testFingerprint(self):
        headers = ['foo', 'bar', 'baz', '012456789', ' ' * 40]

        fingerprints = [
            'afqG6DMhSxO4KpBDUsu56bh2INg',
            'tfw9skV5Y0+l/rfwjzjCjt/cjqY',
            'h4Hss53veo3tdIHjdjsKXqbxrmY',
            'zJVrBypI7Sk46bTy5WPJbikGgGc',
            'vIKcOmXJedx4BUbWwN/u3xohzTA',
        ]
        for (i, header) in enumerate(headers):
            calculated = Cookie.make_fingerprint(headers[:i+1])
            self.assertEqual(calculated, fingerprints[i])

        fingerprints = [
            'vIKcOmXJedx4BUbWwN/u3xohzTA',
            'vYzrXyiBag83ut1pRtRsmjZVxUI',
            '4sWBNkCH3NK6xnOqaLOoEY8kIc8',
            'BJ5xPBh0C9zby06hUTz9zUMdQVE',
            'yejQZ5jg5Lc35uit/xLz8oAmAN4',
        ]
        for (i, header) in enumerate(headers):
            calculated = Cookie.make_fingerprint(headers[i:])
            self.assertEqual(calculated, fingerprints[i])

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
