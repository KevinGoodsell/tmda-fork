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

"""Generic TMDA pending queue class.

For reference, 'mailid' refers to the unique identifier of a mail
message in the pending queue.  It's a string consisting of two numbers
seperated by a dot, e.g, "1159383896.4198".  This infomration
currently comes from a timestamp and the Python process id.
"""

from TMDA import Defaults
from TMDA import Errors


class Queue:
    def __init__(self):
	self.format = "not defined"

    # Subclasses are expected to override the following methods since
    # their implementation is specific to the format of the queue.

    def exists(self):
	"""
	Return true if the queue exists, otherwise False.
	"""
	pass


    def _create(self):
        """
	Create the queue.
	"""
	pass


    def _convert(self):
	"""
	Convert the existing queue as necessary to a different format.
	JRM: unsure if this method will stay or not.
	"""
	pass


    def cleanup(self):
	"""
	Delete messages from the queue that are older than
	Defaults.PENDING_LIFETIME.
	"""
	pass


    def fetch_ids(self):
	"""
	Return a list containing the just the ids of all messages in
	the queue. e.g, ['1159387731.4602', '1159383896.4198']
	"""
	pass

    
    def insert_message(self, msg, mailid, recipient):
	"""
	Insert the contents of a message into the queue.

	msg is an email.message like object.

	mailid (see above)

	recipient is the recipient e-mail address of this message.
	"""
	pass


    def fetch_message(self, mailid, fullParse=False):
	"""
	Fetch the contents of a message in the queue.  Should
	return an email.message like object.
	Normally uses HeaderParser' for a quick parse unless 'fullParse'
	is set to True, in which case it uses the full 'email.parser'.
	"""
	pass


    def delete_message(self, mailid):
	"""
	Delete a message in the queue.
	"""
	pass


    def find_message(self, mailid):
	"""
	Return true if this message is in the queue, otherwise False.
	"""
	pass


    # Subclasses should not override this method.

    def init(self):
	qformat = Defaults.PENDING_QUEUE_FORMAT
	if qformat.lower() == 'original':
	    from OriginalQueue import OriginalQueue
	    return OriginalQueue()
	if qformat.lower() == 'maildir':
	    from MaildirQueue import MaildirQueue
	    return MaildirQueue()
	else:
	    raise Errors.ConfigError, \
		"Unknown PENDING_QUEUE_FORMAT: " + '"%s"' % qformat

