# -*- python -*-

"""Mail Transfer Agent (MTA) related objects."""


import os
import string
import sys

import Defaults


class MTA:
    """Methods and instance variables common to all MTAs. """
    def __init__(self):
        pass
       
class Postfix(MTA):
    """Postfix-specific methods and instance variables."""
    def __init__(self):
        MTA.__init__(self)
        # Postfix exit status codes; see /usr/include/sysexits.h
        self.EX_HARD = 77               # permission denied; bounce message
        self.EX_OK = 0                  # successful termination; exit
        self.EX_STOP = None             # Postfix doesn't have such an exit code
        self.EX_TEMPFAIL = 75           # temporary failure; defer delivery
    # Define the four states of a message.
    def bounce(self):
        sys.exit(self.EX_HARD)
    def defer(self):
        sys.exit(self.EX_TEMPFAIL)
    def stop(self):
        sys.exit(self.EX_OK)
    def deliver(self, message=None):
        self.local_delivery_agent = Defaults.LOCAL_DELIVERY_AGENT
        self.__pipeline = os.popen(self.local_delivery_agent, 'w')
        self.__pipeline.write(message)
        self.__pipeline.close()
        sys.exit()


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
    def deliver(self, message=None):
        sys.exit(self.EX_OK)


def init():
    """Factory function which determine what MTA we are running and
    instantiates the corresponding MTA subclass."""
    my_mta = string.capitalize(Defaults.MAIL_TRANSFER_AGENT)
    if my_mta == 'Postfix':
        return Postfix()
    elif my_mta == 'Qmail':
        return Qmail()
    else:
        print "Unsupported MTA",my_mta
        sys.exit(Defaults.EX_TEMPFAIL)
