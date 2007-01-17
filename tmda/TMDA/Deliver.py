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

"""TMDA local mail delivery."""


import fcntl
import os
import signal
import socket
import stat
import sys
import time

import Defaults
import Errors
import Util


def alarm_handler(signum, frame):
    """Handle an alarm."""
    print 'Signal handler called with signal', signum
    raise IOError, "Couldn't open device!"


def lock_file(fp):
    """Do fcntl file locking."""
    fcntl.flock(fp.fileno(), fcntl.LOCK_EX)


def unlock_file(fp):
    """Do fcntl file unlocking."""
    fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


class Deliver:
    def __init__(self, msg, delivery_option):
        """
        msg is an email.message object.

        deliver_option is a delivery action option string returned
        from the TMDA.FilterParser instance.
        """
        self.msg = msg
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
        # An mmdf line begins with a : 
        elif firstchar == ':':
            self.delivery_type = 'mmdf'
            self.delivery_dest = self.option[1:].strip()
            if self.delivery_dest.startswith('~'):
                self.delivery_dest = os.path.expanduser(self.delivery_dest)
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
        elif self.option == '_filter_':
            self.delivery_type = 'filter'
            self.delivery_dest = 'stdout'
        # Unknown delivery instruction.
        else:
            raise Errors.DeliveryError, \
                  'Delivery instruction "%s" is not recognized!' % self.option
        return (self.delivery_type, self.delivery_dest)

    def deliver(self):
        """Deliver the message appropriately."""
        # Optionally, remove some headers.
        Util.purge_headers(self.msg, Defaults.PURGED_HEADERS_DELIVERY)
        (type, dest) = self.get_instructions()
        if type == 'program':
            # don't wrap headers, don't escape From, add From_ line
            self.__deliver_program(Util.msg_as_string(self.msg, 0, 0, 1),
                                   dest)
        elif type == 'forward':
            # don't wrap headers, don't escape From, don't add From_ line
            self.__deliver_forward(Util.msg_as_string(self.msg), dest)
        elif type == 'mmdf':
            # Ensure destination path exists.
            if not os.path.exists(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" does not exist!' % dest
            # Refuse to deliver to an mmdf if it's a symlink, to
            # prevent symlink attacks.
            elif os.path.islink(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" is a symlink!' % dest
            else:
                # don't wrap headers, escape From, add From_ line
                self.__deliver_mmdf(Util.msg_as_string(self.msg, 0, 1, 1),
                                    dest)
        elif type == 'mbox':
            # Ensure destination path exists.
            if not os.path.exists(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" does not exist!' % dest
            # Refuse to deliver to an mbox if it's a symlink, to
            # prevent symlink attacks.
            elif os.path.islink(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" is a symlink!' % dest
            else:
                # don't wrap headers, escape From, add From_ line
                self.__deliver_mbox(Util.msg_as_string(self.msg, 0, 1, 1),
                                    dest)
        elif type == 'maildir':
            # Ensure destination path exists.
            if not os.path.exists(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" does not exist!' % dest
            else:
                # don't wrap headers, don't escape From, don't add From_ line
                self.__deliver_maildir(Util.msg_as_string(self.msg), dest)
        elif type == 'filter':
            sys.stdout.write(Util.msg_as_string(self.msg))

    def __deliver_program(self, message, program):
        """Deliver message to /bin/sh -c program."""
        Util.pipecmd(program, message)

    def __deliver_forward(self, message, address):
        """Forward message to address, preserving the existing Return-Path."""
        Util.sendmail(message, address, self.env_sender)
        
    def __deliver_mmdf(self, message, mmdf):
        """Reliably deliver a mail message into an mmdf file.

        Basicly a copy of __deliver_mbox():
        Just make sure each message is surrounded by "\1\1\1\1\n"
        """
        try:
	    # When orig_length is None, we haven't opened the file yet.
            orig_length = None
            # Open the mmdf file.
            fp = open(mmdf, 'rb+')
            lock_file(fp)
            status_old = os.fstat(fp.fileno())
            # Check if it _is_ an mmdf file; mmdf files must start
            # with "\1\1\1\1\n" in their first line, or are 0-length files.
            fp.seek(0, 0)                # seek to start
            first_line = fp.readline()
            if first_line != '' and first_line[:5] != '\1\1\1\1\n':
                # Not an mmdf file; abort here.
                unlock_file(fp)
                fp.close()
                raise Errors.DeliveryError, \
                      'Destination "%s" is not an mmdf file!' % mmdf
            fp.seek(0, 2)                # seek to end
            orig_length = fp.tell()      # save original length
            fp.write('\1\1\1\1\n')
            # Add a trailing newline if last line incomplete.
            if message[-1] != '\n':
                message = message + '\n'
            # Write the message.
            fp.write(message)
            # Add a trailing blank line.
            fp.write('\n')
            fp.write('\1\1\1\1\n')
            fp.flush()
            os.fsync(fp.fileno())
            # Unlock and close the file.
            status_new = os.fstat(fp.fileno())
            unlock_file(fp)
            fp.close()
            # Reset atime.
            os.utime(mmdf, (status_old[stat.ST_ATIME], status_new[stat.ST_MTIME]))
        except IOError, txt:
            try:
                if not fp.closed and not orig_length is None:
		    # If the file was opened and we know how long it was,
		    # try to truncate it back to that length.
                    fp.truncate(orig_length)
                unlock_file(fp)
                fp.close()
            except:
                pass
            raise Errors.DeliveryError, \
                  'Failure writing message to mmdf file "%s" (%s)' % (mmdf, txt)

    def __deliver_mbox(self, message, mbox):
        """Reliably deliver a mail message into an mboxrd-format mbox file.

        See <URL:http://www.qmail.org/man/man5/mbox.html>
        
        Based on code from getmail
        <URL:http://www.qcc.sk.ca/~charlesc/software/getmail-2.0/>
        Copyright (C) 2001 Charles Cazabon, and licensed under the GNU
        General Public License version 2.
        """
        try:
	    # When orig_length is None, we haven't opened the file yet.
            orig_length = None
            # Open the mbox file.
            fp = open(mbox, 'rb+')
            lock_file(fp)
            status_old = os.fstat(fp.fileno())
            # Check if it _is_ an mbox file; mbox files must start
            # with "From " in their first line, or are 0-length files.
            fp.seek(0, 0)                # seek to start
            first_line = fp.readline()
            if first_line != '' and first_line[:5] != 'From ':
                # Not an mbox file; abort here.
                unlock_file(fp)
                fp.close()
                raise Errors.DeliveryError, \
                      'Destination "%s" is not an mbox file!' % mbox
            fp.seek(0, 2)                # seek to end
            orig_length = fp.tell()      # save original length
            # Add a trailing newline if last line incomplete.
            if message[-1] != '\n':
                message = message + '\n'
            # Write the message.
            fp.write(message)
            # Add a trailing blank line.
            fp.write('\n')
            fp.flush()
            os.fsync(fp.fileno())
            # Unlock and close the file.
            status_new = os.fstat(fp.fileno())
            unlock_file(fp)
            fp.close()
            # Reset atime.
            os.utime(mbox, (status_old[stat.ST_ATIME], status_new[stat.ST_MTIME]))
        except IOError, txt:
            try:
                if not fp.closed and not orig_length is None:
		    # If the file was opened and we know how long it was,
		    # try to truncate it back to that length.
                    fp.truncate(orig_length)
                unlock_file(fp)
                fp.close()
            except:
                pass
            raise Errors.DeliveryError, \
                  'Failure writing message to mbox file "%s" (%s)' % (mbox, txt)

    def __deliver_maildir(self, message, maildir):
        """Reliably deliver a mail message into a Maildir.

        See <URL:http://cr.yp.to/proto/maildir.html> and
            <URL:http://www.qmail.org/man/man5/maildir.html>

        Uses code from getmail
        <URL:http://www.qcc.sk.ca/~charlesc/software/getmail-2.0/>
        Copyright (C) 2001 Charles Cazabon, and licensed under the GNU
        General Public License version 2.
        """
        # (same as Postfix)
        # 1. Create    tmp/time.P<pid>.hostname
        # 2. Rename to new/time.V<device>I<inode>.hostname
        #
        # When creating a file in tmp/ we use the process-ID because
        # it's still an exclusive resource. When moving the file to
        # new/ we use the device number and inode number.
        #
        # IEEE Std 1003.1-2001 (Open Group Base Specifications Issue
        # 6, "SUS # v3") claims (in the section on <sys/stat.h>) that
        # st_ino and st_dev together uniquely identify a file within
        # a system.
        #
        # djb says that inode numbers and device numbers aren't always
        # available through NFS, but this shouldn't be the case if the
        # NFS implementation is POSIX compliant.
        
        # Set a 24-hour alarm for this delivery.
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(24 * 60 * 60)

        dir_tmp = os.path.join(maildir, 'tmp')
        dir_cur = os.path.join(maildir, 'cur')
        dir_new = os.path.join(maildir, 'new')
        if not (os.path.isdir(dir_tmp) and 
                os.path.isdir(dir_cur) and
                os.path.isdir(dir_new)):
            raise Errors.DeliveryError, 'not a Maildir! (%s)' % maildir

        now = time.time()
        pid = os.getpid()

        hostname = socket.gethostname()
        # To deal with invalid host names.
        hostname = hostname.replace('/', '\\057').replace(':', '\\072')
        
        # e.g, 1043715037.P28810.hrothgar.la.mastaler.com
        filename_tmp = '%lu.P%d.%s' % (now, pid, hostname)
        fname_tmp = os.path.join(dir_tmp, filename_tmp)
        # File must not already exist.
        if os.path.exists(fname_tmp):
            raise Errors.DeliveryError, fname_tmp + 'already exists!'
        
        # Get user & group of maildir.
        s_maildir = os.stat(maildir)
        maildir_owner = s_maildir[stat.ST_UID]
        maildir_group = s_maildir[stat.ST_GID]

        # Open file to write.
        try:
            fd = os.open(fname_tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0600)
            fp = os.fdopen(fd, 'wb', 4096)
            os.chmod(fname_tmp, 0600)
            try:
                # If root, change the message to be owned by the
                # Maildir owner
                os.chown(fname_tmp, maildir_owner, maildir_group)
            except OSError:
                # Not running as root, can't chown file.
                pass
            fp.write(message)
            fp.flush()
            os.fsync(fp.fileno())
            fp.close()
        except (OSError, IOError), o:
            signal.alarm(0)
            raise Errors.DeliveryError, \
                  'Failure writing file %s (%s)' % (fname_tmp, o)

        fstatus = os.stat(fname_tmp)
        # e.g, 1043715037.V20d04I18bfb.hrothgar.la.mastaler.com
        filename_new = '%lu.V%lxI%lx.%s' % (now, fstatus[stat.ST_DEV],
                                            fstatus[stat.ST_INO], hostname)
        fname_new = os.path.join(dir_new, filename_new)
        # File must not already exist.
        if os.path.exists(fname_new):
            raise Errors.DeliveryError, fname_new + 'already exists!'
        
        # Move message file from Maildir/tmp to Maildir/new
        try:
            os.link(fname_tmp, fname_new)
            os.unlink(fname_tmp)
        except OSError:
            signal.alarm(0)
            try:
                os.unlink(fname_tmp)
            except:
                pass
            raise Errors.DeliveryError, 'failure renaming "%s" to "%s"' \
                   % (fname_tmp, fname_new)

        # Delivery is done, cancel the alarm.
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
