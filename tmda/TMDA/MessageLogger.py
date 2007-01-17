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

"""
Log statistics about incoming or outgoing messages to a file.
"""


from email.utils import parseaddr

import Util


class MessageLogger:
    def __init__(self, logfile, msg, **vardict):
        """
        logfile is the full path to the logfile.
        
        msg in an email.message object.

        vardict is a dictionary containing an indefinite number of
        keyword arguments.
        """
        self.msg = msg
        self.vardict = vardict
        self.logfile = logfile
        self.log = open(self.logfile, 'a')

    def write(self):
        """
        Write a log entry for this message in a common format.

        Date: (timestamp)
        XPri: (X-Primary-Address header if present)
        Sndr: (envelope sender address if different than From)
        From: (From header)
        Rept: (Reply-To header if present)
          To: (envelope recipient address)
        Subj: (Subject header)
        Actn: (message trigger and size of message)
        """
        self.__writeline('Date', Util.make_date())
        XPri = self.msg.get('x-primary-address')
        if XPri:
            self.__writeline('XPri', XPri)
        envsender = self.vardict.get('envsender', None)
        if (envsender
            and parseaddr(self.msg.get('from'))[1] != envsender):
            self.__writeline('Sndr', envsender)
        From = self.msg.get('from')
        if From:
            self.__writeline('From', From)
        ReplyTo = self.msg.get('reply-to')
        if ReplyTo:
            self.__writeline('Rept', ReplyTo)
        self.__writeline('To', self.vardict.get('envrecip'))
        self.__writeline('Subj', self.msg.get('subject'))
        Action = self.vardict.get('action_msg')
        sizestr = '(%s)' % self.vardict.get('msg_size')
        wsbuf = 72 - len(Action) - len(sizestr)
        Action = Action + ' '*wsbuf + sizestr # 78 chars max
        self.__writeline('Actn', Action)
        self.__close()

    def __writeline(self, name, value):
        self.log.write('%s: %s\n' % (name.rjust(4), value))

    def __close(self):
        self.log.write('\n')
        self.log.close()
