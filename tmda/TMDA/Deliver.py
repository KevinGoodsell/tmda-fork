# -*- python -*-

"""TMDA local mail delivery."""


import os

import Defaults
import Errors
import Util


class Deliver:
    def __init__(self, headers, body, delivery_option):
        """
        headers is an rfc822.Message instance.

        body is the message content from that instance.

        deliver_option is a delivery action option string returned
        from the TMDA.FilterParser instance.
        """
        self.headers = headers
        self.body = body
        self.message = str(headers) + '\n' + body
        self.option = delivery_option
        self.env_sender = os.environ.get('SENDER')
        
    def get_instructions(self):
        """Process the delivery_option string, returning a tuple
        containing the type of delivery to be performed, and the
        normalized delivery destination.  e.g,

        ('forward', 'me@new.job.com')
        """
        self.delivery_type = self.delivery_dest = None
        firstchar = self.option[0]
        lastchar = self.option[-1]
        # A program line begins with a vertical bar.
        if firstchar == '|':
            self.delivery_type = 'program'
            self.delivery_dest = self.option[1:].strip()
        # A forward line begins with an ampersand.  If the address
        # begins with a letter or number, you may leave out the
        # ampersand.
        elif firstchar == '&' or firstchar.isalnum():
            self.delivery_type = 'forward'
            self.delivery_dest = self.option
            if firstchar == '&':
                self.delivery_dest = self.delivery_dest[1:].strip()
        # An mbox line begins with a slash or tilde, and does not end
        # with a slash.
        elif (firstchar == '/' or firstchar == '~') and (lastchar != '/'):
            self.delivery_type = 'mbox'
            self.delivery_dest = self.option
            if firstchar == '~':
                self.delivery_dest = os.path.expanduser(self.delivery_dest)
        # A maildir line begins with a slash or tilde and ends with a
        # slash.
        elif (firstchar == '/' or firstchar == '~') and (lastchar == '/'):
            self.delivery_type = 'maildir'
            self.delivery_dest = self.option
            if firstchar == '~':
                self.delivery_dest = os.path.expanduser(self.delivery_dest)
        # Unknown delivery instruction.
        else:
            raise Errors.DeliveryError, \
                  'Delivery instruction "%s" is not recognized!' % self.option
        return (self.delivery_type, self.delivery_dest)

    def deliver(self):
        """Deliver the message appropriately."""
        (type, dest) = self.get_instructions()
        if type == 'program':
            self.__deliver_program(self.message, dest)
        elif type == 'forward':
            self.__deliver_forward(self.headers, self.body, dest)
        elif type == 'mbox':
            self.__deliver_mbox(self.message, dest)
        elif type == 'maildir':
            self.__deliver_maildir(self.message, dest)

    def __deliver_program(self, message, program):
        """Deliver message to /bin/sh -c program."""
        Util.pipecmd(program, message)

    def __deliver_forward(self, headers, body, address):
        """Forward message to address, preserving the existing Return-Path."""
        Util.sendmail(headers, body, address, self.env_sender)
        
    def __deliver_mbox(self, message, mbox):
        """ """
        raise Errors.DeliveryError, \
              'mbox delivery not yet implemented!'

    def __deliver_maildir(self, message, maildir):
        """ """
        raise Errors.DeliveryError, \
              'Maildir delivery not yet implemented!'
