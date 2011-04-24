import unittest
import sys
import time
import os
import cStringIO as StringIO
from email.parser import Parser

import lib.util
lib.util.testPrep()

from TMDA import Pending
from TMDA import Defaults
from TMDA import Util

verbose = False

test_messages = {
    '1243439251.12345' : [
        'X-TMDA-Recipient: testuser@nowhere.com',
        'Return-Path: <message1@return.path.com>',
        'Message-ID: <12345@mail.somewhere.org>',
        'Subject: Test message number one!',
        '',
        'This is a test message.',
    ],
    '1303349951.12346' : [
        'X-TMDA-Recipient: testuser@nowhere.com',
        'Return-Path: <message2@return.path.com>',
        'Message-ID: <12346@mail.somewhere.org>',
        'Subject: Test message number TWO!',
        '',
        'This is another test message.',
    ],
    '1303433207.12347' : [
        'X-TMDA-Recipient: testuser-extension@nowhere.com',
        'Return-Path: <message3@return.path.com>',
        'Message-ID: <12347@mail.somewhere.org>',
        'Subject: Test message number last.',
        '',
        'This is the last',
        'test',
        'message',
    ],
}

class MockMailQueue(object):
    parser = Parser()

    def __init__(self):
        self._msgs = {}

        for (msgid, body) in test_messages.items():
            self._msgs[msgid] = '\r\n'.join(body)

    def init(self):
        return self

    def exists(self):
        return True

    def fetch_ids(self):
        return self._msgs.keys()

    def find_message(self, msgid):
        return msgid in self._msgs

    def fetch_message(self, msgid, fullParse=False):
        headers_only = not fullParse
        return self.parser.parsestr(self._msgs[msgid], headers_only)

    def delete_message(self, msgid):
        self._msgs.pop(msgid, None)

class QueueInitTests(unittest.TestCase):
    '''
    Basic tests for initializing TMDA.Pending.Queue.
    '''

    def setUp(self):
        Pending.Q = MockMailQueue()

    # Three types of initialization:

    def testInitQueueFromParams(self):
        # With a list provided, only those specific message IDs should be
        # present.
        pending = Pending.Queue(['11243439251.2345', '1303433207.12347'])
        pending.initQueue()
        self.assertEqual(pending.msgs, ['11243439251.2345', '1303433207.12347'])

    def testInitQueueFromStdin(self):
        saved_stdin = sys.stdin
        try:
            # With a '-', IDs should be read from stdin.
            sys.stdin = StringIO.StringIO(
                '1303349951.12346\n1243439251.12345\n')
            pending = Pending.Queue(['-'])
            pending.initQueue()
            self.assertEqual(pending.msgs, ['1243439251.12345',
                                            '1303349951.12346'])

            # With a '-' in combo with IDs, should include both stdin and the
            # specified IDs.
            sys.stdin = StringIO.StringIO('1303349951.12346\n')
            pending = Pending.Queue(['-', '1303433207.12347'])
            pending.initQueue()
            self.assertEqual(pending.msgs, ['1303349951.12346',
                                            '1303433207.12347'])
        finally:
            sys.stdin = saved_stdin

    def testInitQueueFromPending(self):
        # With no arguments, everything from the pending queue should be
        # included.
        pending = Pending.Queue()
        pending.initQueue()
        self.assertEqual(pending.msgs, ['1243439251.12345', '1303349951.12346',
                                        '1303433207.12347'])

class QueueLoopTestMixin(object):
    expected_addrs = ['message1@return.path.com', 'message2@return.path.com',
                      'message3@return.path.com']
    db_params = dict(recipient='testuser@nowhere.com', username='testuser',
                     hostname='nowhere.com')

    def setUp(self):
        self.file_appends = []
        self.db_inserts = []
        self.pager_calls = []

        Util.append_to_file = self.recordFileAppend
        Util.db_insert = self.recordDbInsert
        Util.pager = self.nullPager

        Defaults.PENDING_WHITELIST_APPEND = 'whitelist_file'
        Defaults.PENDING_BLACKLIST_APPEND = 'blacklist_file'
        Defaults.PENDING_RELEASE_APPEND = 'release_file'
        Defaults.PENDING_DELETE_APPEND = 'delete_file'

        Defaults.DB_CONNECTION = 'db_connection'

        Defaults.DB_PENDING_WHITELIST_APPEND = 'whitelist_db_stmt'
        Defaults.DB_PENDING_BLACKLIST_APPEND = 'blacklist_db_stmt'
        Defaults.DB_PENDING_RELEASE_APPEND = 'release_db_stmt'
        Defaults.DB_PENDING_DELETE_APPEND = 'delete_db_stmt'

        # This changes the results of the whitelist tests, and isn't very
        # necessary since there's a separate release test anyway.
        Defaults.PENDING_WHITELIST_RELEASE = False

        Pending.Q = MockMailQueue()

    def tearDown(self):
        # Remove pending cache
        try:
            os.remove(Defaults.PENDING_CACHE)
        except:
            pass

        del Defaults.PENDING_WHITELIST_APPEND
        del Defaults.PENDING_BLACKLIST_APPEND
        del Defaults.PENDING_RELEASE_APPEND
        del Defaults.PENDING_DELETE_APPEND
        del Defaults.DB_CONNECTION
        del Defaults.DB_PENDING_WHITELIST_APPEND
        del Defaults.DB_PENDING_BLACKLIST_APPEND
        del Defaults.DB_PENDING_RELEASE_APPEND
        del Defaults.DB_PENDING_DELETE_APPEND
        del Defaults.PENDING_WHITELIST_RELEASE

        reload(Defaults)
        reload(Util)

    # DERIVED CLASS OVERRIDES
    dispose = None

    def dropFileAppend(self):
        '''Add options for appending to a file'''
        raise NotImplementedError()

    def dropDbInsert(self):
        '''Add options for inserting into a database'''
        raise NotImplementedError()

    def expectedFileAppends(self):
        return [(addr, self.append_file) for addr in self.expected_addrs]

    def expectedDbInserts(self):
        result = []
        for addr in self.expected_addrs:
            params = dict(self.db_params)
            params['sender'] = addr
            result.append(('db_connection', self.insert_stmt, params))

        return result

    # UTILITIES
    def recordFileAppend(self, *args):
        self.file_appends.append(args)

    def recordDbInsert(self, *args):
        self.db_inserts.append(args)

    def nullPager(self, *args):
        pass

    # TESTS
    def testFileAppend(self):
        queue = Pending.Queue(dispose=self.dispose, verbose=verbose)
        queue.initQueue()

        self.dropDbInsert()

        queue.mainLoop()
        self.assertEqual(self.file_appends, self.expectedFileAppends())
        self.assertEqual(self.db_inserts, [])

    def testDbAppend(self):
        queue = Pending.Queue(dispose=self.dispose, verbose=verbose)
        queue.initQueue()

        self.dropFileAppend()

        queue.mainLoop()
        self.assertEqual(self.file_appends, [])
        self.assertEqual(self.db_inserts, self.expectedDbInserts())

    def testBothAppend(self):
        queue = Pending.Queue(dispose=self.dispose, verbose=verbose)
        queue.initQueue()

        queue.mainLoop()
        self.assertEqual(self.file_appends, self.expectedFileAppends())
        self.assertEqual(self.db_inserts, self.expectedDbInserts())

    def testPretend(self):
        queue = Pending.Queue(dispose=self.dispose, verbose=verbose,
                              pretend=True)
        queue.initQueue()

        queue.mainLoop()
        self.assertEqual(self.file_appends, [])
        self.assertEqual(self.db_inserts, [])


# This version of the QueueLoopTestMixin is to be used with dispose methods that
# actually do append to a file and/or database (not 'show' or 'pass')
class QueueLoopTestAppendingMixin(QueueLoopTestMixin):
    # Threshold tests are in a separate mixin because nothing happens in cases
    # like 'pass' and 'show', so there's nothing to check.
    def testThresholdYounger(self):
        threshold = "%ds" % (time.time() - 1280000000)

        queue = Pending.Queue(dispose=self.dispose, verbose=verbose,
                              threshold=threshold, younger=True)
        queue.initQueue()

        queue.mainLoop()
        self.assertEqual(len(self.file_appends), 2)
        self.assertEqual(len(self.db_inserts), 2)

    def testThresholdOlder(self):
        threshold = "%ds" % (time.time() - 1280000000)

        queue = Pending.Queue(dispose=self.dispose, verbose=verbose,
                              threshold=threshold, older=True)
        queue.initQueue()

        queue.mainLoop()
        self.assertEqual(len(self.file_appends), 1)
        self.assertEqual(len(self.db_inserts), 1)

    def testCached(self):
        # First, cause some IDs to be cached.
        cache_ids = ['1243439251.12345', '1303433207.12347']
        queue = Pending.Queue(cache_ids, cache=True, dispose='pass',
                              verbose=verbose)
        queue.initQueue()

        queue.mainLoop()
        # Make sure the cached IDs are as expected.
        self.assertEqual(queue.msgcache, list(reversed(cache_ids)))

        # Revisit the loop, this time expected only the non-cached IDs to be
        # handled.
        queue = Pending.Queue(cache=True, dispose=self.dispose, verbose=verbose)
        queue.initQueue()

        queue.mainLoop()
        self.assertEqual(len(self.file_appends), 1)
        self.assertEqual(len(self.db_inserts), 1)


class QueueLoopPassTest(QueueLoopTestMixin, unittest.TestCase):
    dispose = 'pass'

    def dropFileAppend(self):
        pass

    def dropDbInsert(self):
        pass

    def expectedFileAppends(self):
        return []

    def expectedDbInserts(self):
        return []

class QueueLoopReleaseTest(QueueLoopTestAppendingMixin, unittest.TestCase):
    dispose = 'release'
    append_file = 'release_file'
    insert_stmt = 'release_db_stmt'

    def dropFileAppend(self):
        Defaults.PENDING_RELEASE_APPEND = None

    def dropDbInsert(self):
        Defaults.DB_PENDING_RELEASE_APPEND = None

class QueueLoopDeleteTest(QueueLoopTestAppendingMixin, unittest.TestCase):
    dispose = 'delete'
    append_file = 'delete_file'
    insert_stmt = 'delete_db_stmt'

    def dropFileAppend(self):
        Defaults.PENDING_DELETE_APPEND = None

    def dropDbInsert(self):
        Defaults.DB_PENDING_DELETE_APPEND = None

class QueueLoopWhitelistTest(QueueLoopTestAppendingMixin, unittest.TestCase):
    dispose = 'whitelist'
    append_file = 'whitelist_file'
    insert_stmt = 'whitelist_db_stmt'

    def dropFileAppend(self):
        Defaults.PENDING_WHITELIST_APPEND = None

    def dropDbInsert(self):
        Defaults.DB_PENDING_WHITELIST_APPEND = None

class QueueLoopBlacklistTest(QueueLoopTestAppendingMixin, unittest.TestCase):
    dispose = 'blacklist'
    append_file = 'blacklist_file'
    insert_stmt = 'blacklist_db_stmt'

    def dropFileAppend(self):
        Defaults.PENDING_BLACKLIST_APPEND = None

    def dropDbInsert(self):
        Defaults.DB_PENDING_BLACKLIST_APPEND = None

class QueueLoopShowTest(QueueLoopTestMixin, unittest.TestCase):
    dispose = 'show'
    append_file = 'unused'
    insert_stmt = 'unused'

    def dropFileAppend(self):
        pass

    def dropDbInsert(self):
        pass

    def expectedFileAppends(self):
        return []

    def expectedDbInserts(self):
        return []


if __name__ == '__main__':
    if '-v' in sys.argv:
        verbose = True
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
