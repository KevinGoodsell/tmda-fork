# -*- python -*-
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
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

"""SMTP direct drop-off.

This module delivers messages via SMTP to a locally specified daemon.
This should be compatible with any modern SMTP server.  It is expected
that the MTA handles all final delivery.

Includes code from Mailman
<URL:http://www.gnu.org/software/mailman/mailman.html>
Copyright (C) 1998,1999,2000,2001 by the Free Software Foundation, Inc.,
and licensed under the GNU General Public License version 2.
"""

import smtplib

import Defaults


# Manage a connection to an SMTP server.
class Connection:
    def __init__(self):
        self.__connect()

    def __connect(self):
        self.__conn = smtplib.SMTP()
        self.__conn.connect(Defaults.SMTPHOST)
        self.__numsessions = Defaults.SMTP_MAX_SESSIONS_PER_CONNECTION
        # Optional SMTP Authentication.
        if Defaults.SMTPAUTH_USERNAME and Defaults.SMTPAUTH_PASSWORD:
            self.__conn.login(Defaults.SMTPAUTH_USERNAME,
                              Defaults.SMTPAUTH_PASSWORD)
            
    def sendmail(self, envsender, recips, msgtext):
        try:
            results = self.__conn.sendmail(envsender, recips, msgtext)
        except smtplib.SMTPException:
            # For safety, reconnect.
            self.__conn.quit()
            self.__connect()
            # Let exceptions percolate up.
            raise
        # Decrement the session counter, reconnecting if necessary.
        self.__numsessions -= 1
        # By testing exactly for equality to 0, we automatically
        # handle the case for SMTP_MAX_SESSIONS_PER_CONNECTION <= 0
        # meaning never close the connection.  We won't worry about
        # wraparound <wink>.
        if self.__numsessions == 0:
            self.__conn.quit()
            self.__connect()
        return results

    def quit(self):
        self.__conn.quit()

