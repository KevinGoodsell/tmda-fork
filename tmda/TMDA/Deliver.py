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

"""TMDA local mail delivery."""


import os
import signal
import socket
import stat
import time

import Defaults
import Errors
import Util


def alarm_handler(signum, frame):
    """Handle an alarm."""
    print 'Signal handler called with signal', signum
    raise IOError, "Couldn't open device!"


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
            if os.path.exists(dest):
                self.__deliver_maildir(self.message, dest)
            else:
                raise Errors.DeliveryError, \
                      'Destination "%s" does not exist!' % dest

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
        """Reliably deliver a mail message into a Maildir.

        See <URL:http://www.qmail.org/man/man5/maildir.html>

        Based on code from getmail
        <URL:http://www.qcc.sk.ca/~charlesc/software/getmail-2.0/>
        Copyright (C) 2001 Charles Cazabon, and licensed under the GNU
        General Public License version 2.
        """
        # e.g, 1014754642.51195.aguirre.la.mastaler.com
        filename = '%s.%s.%s' % (int(time.time()), Defaults.PID,
                                 socket.gethostname())
        # Set a 24-hour alarm for this delivery.
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(24 * 60 * 60)

        dir_tmp = os.path.join(maildir, 'tmp')
        dir_new = os.path.join(maildir, 'new')
        if not (os.path.isdir(dir_tmp) and os.path.isdir(dir_new)):
            raise Errors.DeliveryError, 'not a Maildir! (%s)' % maildir

        fname_tmp = os.path.join(dir_tmp, filename)
        fname_new = os.path.join(dir_new, filename)

        # File must not already exist.
        if os.path.exists(fname_tmp):
            raise Errors.DeliveryError, fname_tmp + 'already exists!'
        if os.path.exists(fname_new):
            raise Errors.DeliveryError, fname_new + 'already exists!'

        # Get user & group of maildir.
        s_maildir = os.stat(maildir)
        maildir_owner = s_maildir[stat.ST_UID]
        maildir_group = s_maildir[stat.ST_GID]

        # Open file to write.
        try:
            fp = open(fname_tmp, 'wb')
            try:
                os.chown(fname_tmp, maildir_owner, maildir_group)
            except OSError:
                # Not running as root, can't chown file.
                pass
            os.chmod(fname_tmp, 0600)
            fp.write(message)
            fp.flush()
            os.fsync(fp.fileno())
            fp.close()
        except IOError:
            raise Errors.DeliveryError, 'Failure writing file ' + fname_tmp

        # Move message file from Maildir/tmp to Maildir/new
        try:
            os.link(fname_tmp, fname_new)
            os.unlink(fname_tmp)
        except OSError:
            try:
                os.unlink(fname_tmp)
            except:
                pass
            raise Errors.DeliveryError, 'failure renaming "%s" to "%s"' \
                   % (fname_tmp, fname_new)

        # Cancel the alarm.
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
