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

"""Mail Transfer Agent (MTA) related objects."""


import os
import sys

import Defaults
import Deliver
import Errors
import Util


class MTA:
    """Non-qmail methods and instance variables. """
    def __init__(self):
        # Exit status codes; see /usr/include/sysexits.h
        self.EX_HARD = 77               # permission denied; bounce message
        self.EX_OK = 0                  # successful termination; exit
        self.EX_STOP = None             # Non-qmail MTAs don't have such an exit code
        self.EX_TEMPFAIL = 75           # temporary failure; defer delivery
        
    # Define the four states of a message.
    def bounce(self):
        sys.exit(self.EX_HARD)

    def defer(self):
        sys.exit(self.EX_TEMPFAIL)

    def stop(self):
        sys.exit(self.EX_OK)

    def deliver(self, headers, body, instruction=None):
        if instruction is None:
            instruction = Defaults.DELIVERY
        msg = Deliver.Deliver(headers, body, instruction)
        msg.deliver()
        self.stop()
            

class Exim(MTA):
    """Exim-specific methods and instance variables."""
    def __init__(self):
        MTA.__init__(self)


class Postfix(MTA):
    """Postfix-specific methods and instance variables."""
    def __init__(self):
        MTA.__init__(self)


class Qmail(MTA):
    """qmail-specific methods and instance variables."""
    def __init__(self):
        MTA.__init__(self)
        # qmail exit status codes; see qmail-command(8)
        self.EX_HARD = 100              # hard error; bounce message
        self.EX_OK = 0                  # success; process next instruction
        self.EX_STOP = 99               # success; ignore further instructions
        self.EX_TEMPFAIL = 111          # soft error; defer delivery

    # Define the four states of a message.
    def bounce(self):
        sys.exit(self.EX_HARD)

    def defer(self):
        sys.exit(self.EX_TEMPFAIL)

    def stop(self):
        sys.exit(self.EX_STOP)

    def deliver(self, headers, body, instruction=None):
        if instruction is None:
            instruction = Defaults.DELIVERY
        if instruction == '_qok_':
            sys.exit(self.EX_OK)
        else:
            msg = Deliver.Deliver(headers, body, instruction)
            msg.deliver()
            self.stop()


class Sendmail(MTA):
    """Sendmail-specific methods and instance variables."""
    def __init__(self):
        MTA.__init__(self)


def init():
    """Factory function which determine what MTA we are running and
    instantiates the corresponding MTA subclass."""
    mta = Defaults.MAIL_TRANSFER_AGENT
    if mta == 'exim':
        return Exim()
    elif mta == 'postfix':
        return Postfix()
    elif mta == 'qmail':
        return Qmail()
    elif mta == 'sendmail':
        return Sendmail()
    else:
        raise Errors.ConfigError, "Unsupported MAIL_TRANSFER_AGENT: " + mta
