# -*- python -*-

"""Mail Transfer Agent (MTA) related objects."""


import os
import string
import sys

import Defaults


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

    def deliver(self, message=None):
        self.local_delivery_agent = Defaults.LOCAL_DELIVERY_AGENT
        # Make sure the LDA actually exists first.
        lda_path = string.split(string.lstrip(self.local_delivery_agent))[0]
        if not os.path.exists(lda_path):
            print "Nonexistent LOCAL_DELIVERY_AGENT:",lda_path
            self.defer()
        else:
            self.__pipeline = os.popen(self.local_delivery_agent, 'w')
            self.__pipeline.write(message)
            exitcode = self.__pipeline.close()
            if not exitcode:
                exitcode = 0
            signal = exitcode & 0x7f
            exitval = exitcode >> 8
            if signal:
                print "LOCAL_DELIVERY_AGENT died by signal", signal
                self.defer()
            elif exitval == 0:
                self.stop()
            elif exitval >= 64 and exitval <= 78:
                sys.exit(exitval)
            else:
                print "LOCAL_DELIVERY_AGENT unknown exit value", exitval
                self.defer()


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

    def deliver(self, message=None):
        sys.exit(self.EX_OK)


def init():
    """Factory function which determine what MTA we are running and
    instantiates the corresponding MTA subclass."""
    my_mta = string.capitalize(Defaults.MAIL_TRANSFER_AGENT)
    if my_mta == 'Exim':
        return Exim()
    elif my_mta == 'Postfix':
        return Postfix()
    elif my_mta == 'Qmail':
        return Qmail()
    else:
        print "Unsupported MTA",my_mta
        sys.exit(Defaults.EX_TEMPFAIL)
