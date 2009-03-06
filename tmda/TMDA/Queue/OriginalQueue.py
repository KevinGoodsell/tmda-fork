# -*- python -*-
#
# Copyright (C) 2001-2007 Jason R. Mastaler <jason@mastaler.com>
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

"""Original pending queue format.  

The original style TMDA queue is the only option one had under TMDA
1.0.x and early 1.1.x releases. It's simply a single directory of
files, one mail message stored per file, where files are named
"mailid.msg" (e.g, 1159377144.3747.msg).  It almost looks like a
Maildir without subdirectories.  It perhaps offers the best
performance, but since it's a custom format, it can't be accessed and
read with non-TMDA tools so may not be as convenient for users who
wish to monitor the contents of their pending queue.
"""


from email.utils import parseaddr

import glob
import os
import time

from TMDA import Defaults
from TMDA import Util
from TMDA.Queue.Queue import Queue



class OriginalQueue(Queue):
    def __init__(self):
        Queue.__init__(self)
        self.format = "original"


    def exists(self):
        if os.path.exists(Defaults.PENDING_DIR):
            return True
        else:
            return False


    def _create(self):
        if not self.exists():
            os.makedirs(Defaults.PENDING_DIR, 0700)


    def _convert(self):
        pass


    def cleanup(self):
        if not self.exists():
            return
        
        lifetimesecs = Util.seconds(Defaults.PENDING_LIFETIME)
        cwd = os.getcwd()
        os.chdir(Defaults.PENDING_DIR)
        msgs = glob.glob('*.*.msg')
        os.chdir(cwd)

        for msg in msgs:
            now = '%d' % time.time()
            min_time = int(now) - int(lifetimesecs)
            msg_time = int(msg.split('.')[0])
            if msg_time > min_time:
                # skip this message
                continue
            # delete this message
            fpath = os.path.join(Defaults.PENDING_DIR, msg)
            if Defaults.PENDING_DELETE_APPEND:
                try:
                    msgobj = Util.msg_from_file(open(fpath, 'r'))
                except IOError:
                    # in case of concurrent cleanups
                    pass
                else:
                    rp = parseaddr(msgobj.get('return-path'))[1]
                    Util.append_to_file(rp, Defaults.PENDING_DELETE_APPEND)
            try:
                os.unlink(fpath)
            except OSError:
                # in case of concurrent cleanups
                pass


    def fetch_ids(self):
        cwd = os.getcwd()
        os.chdir(Defaults.PENDING_DIR)
        msgs = glob.glob('*.*.msg')
        ids = [i.rstrip('.msg') for i in msgs]
        os.chdir(cwd)
        return ids


    def insert_message(self, msg, mailid, recipient):
        fname = mailid + ".msg"
        # Create ~/.tmda/ and friends if necessary.
        self._create()
        # X-TMDA-Recipient is used by release_pending()
        del msg['X-TMDA-Recipient']
        msg['X-TMDA-Recipient'] = recipient
        # Write ~/.tmda/pending/MAILID.msg
        fcontents = Util.msg_as_string(msg)
        fpath = os.path.join(Defaults.PENDING_DIR, fname)
        Util.writefile(fcontents, fpath)
        del msg['X-TMDA-Recipient']


    def fetch_message(self, mailid, fullParse=False):
        fpath = os.path.join(Defaults.PENDING_DIR, mailid + '.msg')
        msg = Util.msg_from_file(file(fpath, 'r'),fullParse=fullParse)
        return msg


    def delete_message(self, mailid):
        fpath = os.path.join(Defaults.PENDING_DIR, mailid + '.msg')
        os.unlink(fpath)


    def find_message(self, mailid):
        fpath = os.path.join(Defaults.PENDING_DIR, mailid + '.msg')
        if os.path.exists(fpath):
            return True
        else:
            return False
