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

"""Maildir compatible pending queue format.

http://en.wikipedia.org/wiki/Maildir
"""


from email.utils import parseaddr
from glob import glob


import fcntl
import os
import signal
import socket
import stat
import time


from TMDA import Defaults
from TMDA import Errors
from TMDA import Util
from TMDA.Queue.Queue import Queue


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



class MaildirQueue(Queue):
    def __init__(self):
	Queue.__init__(self)
	self.format = "maildir"


    def exists(self):
	if os.path.exists(Defaults.PENDING_DIR):
	    return True
	else:
	    return False


    def _create(self):
	if not self.exists():
	    dirpath = Defaults.PENDING_DIR
	    os.makedirs(os.path.join(dirpath, 'cur'), 0700)
	    os.mkdir(os.path.join(dirpath, 'new'), 0700)
	    os.mkdir(os.path.join(dirpath, 'tmp'), 0700)


    def _convert(self):
	pass


    def cleanup(self):
	if not self.exists():
	    return
	
	lifetimesecs = Util.seconds(Defaults.PENDING_LIFETIME)
	cwd = os.getcwd()
	os.chdir(os.path.join(Defaults.PENDING_DIR, 'new'))
	new_msgs = glob('1*.[0-9]*.*')
	os.chdir(os.path.join(Defaults.PENDING_DIR, 'cur'))
	cur_msgs = glob('1*.[0-9]*.*')
	os.chdir(cwd)
	msgs = new_msgs + cur_msgs

        for msg in msgs:
	    now = '%d' % time.time()
            min_time = int(now) - int(lifetimesecs)
            msg_time = int(msg.split('.')[0])
	    if msg_time > min_time:
                # skip this message
		continue
            # delete this message
	    for f in (os.path.join(Defaults.PENDING_DIR, 'new', msg),
		      os.path.join(Defaults.PENDING_DIR, 'cur', msg)):
		if os.path.exists(f):
		    fpath = f
		    break
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
	os.chdir(os.path.join(Defaults.PENDING_DIR, 'new'))
	new_msgs = glob('1*.[0-9]*.*')
	os.chdir(os.path.join(Defaults.PENDING_DIR, 'cur'))
	cur_msgs = glob('1*.[0-9]*.*')
    	ids = ['.'.join(i.split('.')[:2]) 
	       for i in new_msgs + cur_msgs]
	os.chdir(cwd)
	return ids


    def insert_message(self, msg, mailid, recipient):
	# Create the Maildir if necessary.
	self._create()
	# X-TMDA-Recipient is used by release_pending()
	del msg['X-TMDA-Recipient']
	msg['X-TMDA-Recipient'] = recipient
	# Write message
	time, pid = mailid.split('.')
	self.__deliver_maildir(Util.msg_as_string(msg), time, pid, 
			       Defaults.PENDING_DIR)
	del msg['X-TMDA-Recipient']


    def fetch_message(self, mailid, fullParse=False):
	msgs = (glob(os.path.join(Defaults.PENDING_DIR, 'new/') 
		     + '1*.[0-9]*.*')) + \
		     (glob(os.path.join(Defaults.PENDING_DIR, 'cur/') 
			   + '1*.[0-9]*.*'))
	for m in msgs:
	    if mailid in m:
		msg = Util.msg_from_file(file(m, 'r'),fullParse=fullParse)
		return msg
	else:
	    # couldn't find message, defer and retry until we find it
	    raise IOError, "couldn't locate %s, will retry" % m


    def delete_message(self, mailid):
	msgs = (glob(os.path.join(Defaults.PENDING_DIR, 'new/') 
		     + '1*.[0-9]*.*')) + \
		     (glob(os.path.join(Defaults.PENDING_DIR, 'cur/') 
			   + '1*.[0-9]*.*'))
	for m in msgs:
	    if mailid in m:
		os.unlink(m)


    def find_message(self, mailid):
	cwd = os.getcwd()
	os.chdir(Defaults.PENDING_DIR)
	msgs = glob('new/1*.[0-9]*.*') + glob('cur/1*.[0-9]*.*')

	for i in range(5):
	    for m in msgs:
		if mailid in m:
		    os.chdir(cwd)
		    return True
	    else:
		# retry 5 times in case a MUA moved/renamed the
		# message to cur/ in a non-atomic way.
		time.sleep(0.1)
		msgs = glob('new/1*.[0-9]*.*') + glob('cur/1*.[0-9]*.*')
		continue
	# give up; message is not there
	os.chdir(cwd)
	return False


    def __deliver_maildir(self, message, time, pid, maildir):
        """Reliably deliver a mail message into a Maildir.

	Implementation differs slightly from the one in TMDA.Deliver()
	since we need to maintain the time and pid in the file's name.

	message is the mail message as a string.

	time and pid come from the mailid.

	maildir is the destination Maildir.

        Based on code from getmail
        Copyright (C) 2001 Charles Cazabon, and licensed under the GNU
        General Public License version 2.
        """
        # e.g, 1014754642.51195.aguirre.la.mastaler.com
        filename = '%s.%s.%s' % (time, pid, socket.gethostname())
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
            fd = os.open(fname_tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0600)
            fp = os.fdopen(fd, 'wb', 4096)
            os.chmod(fname_tmp, 0600)
            try:
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

        # Cancel the alarm.
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
