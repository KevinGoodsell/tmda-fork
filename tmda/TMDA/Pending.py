# -*- python -*-
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
#
# Author: David Guerizec <david@guerizec.net>
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

"""Pending messages functions."""


import glob
import os
import sys
import time

import email
import Errors
import Defaults
import Util

class QueueError:
    errorMessage = ''
    def __init__(self, msg = 'Unknown error'):
        self.errorMessage = msg

    def __repr__(self):
        return '%s:\n%s' % (self.__class__, self.errorMessage)

class MessageError(QueueError):
    pass

class Queue:
    """A simple pending queue."""

    def __init__( self,
                  msgs = [],
                  cache = None,
                  command_recipient = None,
                  descending = None,
                  dispose = None,
                  older = None,
                  summary = None,
                  terse = None,
                  threshold = None,
                  verbose = 1,
                  younger = None,
                  pretend = None ):

        self.msgs = msgs
        self.cache = cache
        self.command_recipient = command_recipient
        self.descending = descending
        self.dispose_def = dispose
        self.older = older
        self.summary = summary
        self.terse = terse
        self.threshold = threshold
        self.verbose = verbose
        self.younger = younger
        self.pretend = pretend
        self.wantedstdin = 0

        self.stdout = sys.stdout


    def initQueue(self):
        """Initialize the queue with the given parameters (see __init__)."""
        self.pendingdir = os.path.join(Defaults.DATADIR, 'pending')
        if not os.path.exists(self.pendingdir):
            raise QueueError, QueueError('Pending directory %s does not exist, exiting.' % self.pendingdir)
    
        # Replace any `-' in the message list with those messages provided
        # via standard input.  (Since it's pointless to call it twice,
        # it's safe to remove any subsequent occurrences in the list after
        # processing.)
        for msgid in self.msgs:
            if msgid == '-':
                self.wantedstdin = 1
                for line in sys.stdin.readlines():
                    self.msgs.append(line.strip())
                self.msgs.remove('-')

        if not self.msgs and not self.wantedstdin:
            cwd = os.getcwd()
            os.chdir(self.pendingdir)
            self.msgs = glob.glob('*.*.msg*')
            os.chdir(cwd)
    
        self.msgs.sort()
        if self.descending:
            self.msgs.reverse()

        if self.dispose_def is None:
            self.dispose_def = 'pass'

        return self
    
    def Print(self, *strings):
        """Print one or more strings on self.stdout."""
        for s in strings:
            self.stdout.write(str(s))
        self.stdout.write('\n')

    def cPrint(self, *strings):
        """Conditionally print one or more strings."""
        if self.verbose:
            for s in strings:
                self.stdout.write(str(s))
            self.stdout.write('\n')
        else:
            return

    def listIds(self):
        """Return the full list of message identifiers (both pending
        and delivered)."""
        return self.msgs

    def listConfirmedIds(self):
        """Return the list of messages delivered by confirmation."""
        return filter(lambda x: x.endswith(',C'), self.listIds())

    def listReleasedIds(self):
        """Return the list of messages delivered by release."""
        return filter(lambda x: x.endswith(',R'), self.listIds())

    def listDeliveredIds(self):
        """Return the list of delivered (i.e, confirmed or released)
        messages."""
        return self.listConfirmedIds() + self.listReleasedIds()

    def listPendingIds(self):
        """Return the list of still pending (i.e, not yet confirmed or
        released) messages."""
        return [i for i in self.listIds()
                if not (i.endswith(',C') or i.endswith(',R'))]
        
    
    ## Cache related functions (-C option)
    def _loadCache(self):
        """Load the message cache from disk."""
        if self.cache:
            if os.path.exists(Defaults.PENDING_CACHE):
                self.msgcache = Util.unpickle(Defaults.PENDING_CACHE)
            else:
                self.msgcache = []

    def _addCache(self, msgid):
        """Add a message to the cache."""
        if self.cache:
            if msgid in self.msgcache:
                return 0
            else:
                self.msgcache.insert(0, msgid)
        return 1

    def _delCache(self, msgid):
        """Remove a message from the cache."""
        if self.cache:
            # remove message from cache, or else we
            # won't be prompted for it again
            self.msgcache.remove(msgid)

    def _saveCache(self):
        """Save the cache on disk."""
        if self.cache:
            # Trim tail entries off if necessary, and then save the cache.
            self.msgcache = self.msgcache[:Defaults.PENDING_CACHE_LEN]
            Util.pickleit(self.msgcache, Defaults.PENDING_CACHE)

    ## Threshold (-Y and -O options)
    def checkTreshold(self, msgid):
        """Check the threshold against the message date."""
        if self.threshold:
            threshold_secs = Util.seconds(self.threshold)
            now = '%d' % time.time()
            min_time = int(now) - int(threshold_secs)
            msg_time = int(msgid.split('.')[0])
            if (self.younger and msg_time < min_time) or \
               (self.older and msg_time > min_time):
                # skip this message
                return 0
        return 1

    def checkDelivered(self, M):
        """Check if the message has already been delivered."""
        if M.wasDelivered():
            if self.dispose_def == 'delete':
                # pretend it isn't delivered if we want to delete
                # old message, else delivered messages will never
                # be removed from disk
                return 0
            return 1
        return 0

    def disposeMessage(self, M):
        """Dispose the message."""
        if not self.pretend:
            if self.dispose == 'release':
                M.release()
            elif self.dispose == 'delete':
                M.delete()
            elif self.dispose == 'whitelist':
                M.whitelist()
            elif self.dispose == 'blacklist':
                M.blacklist()
            elif self.dispose == 'pass':
                return 0
            elif self.dispose == 'show':
                self.Print(M.pager())
        return 1

    def processMessage(self, M):
        """This is a callback for inherited classes."""
        self.showMessage(M)
        return 1
            
    def showMessage(self, M):
        """Display a message."""
        if self.summary or not self.terse:
            self.Print()
            self.Print(M.summary(self.count, self.total, self.summary))
        if self.terse:
            self.Print('\t'.join(M.terse()))

    ## Pure virtual method (to be used by InteractiveQueue)
    def endProcessMessage(self, M):
        """Pure virtual method to be overriden by inherited classes."""
        pass

    ## Main loop
    def mainLoop(self):
        """Process all the messages."""
    
        self.total = len(self.msgs)
        self.count = 0
        
        self.dispose = self.dispose_def
    
        self._loadCache()
            
        for msgid in self.msgs:
            self.count = self.count + 1
            try:
                M = Message(msgid, self.command_recipient)
            except MessageError, obj:
                self.cPrint(obj)
                continue

            if self.checkDelivered(M):
                continue
            if not self.checkTreshold(M.msgid):
                continue
            if not self._addCache(M.msgid):
                continue

            # Pass over the message if it lacks X-TMDA-Recipient and we
            # aren't using `-R'.
            if not M.getConfirmAddress():
                self.cPrint("can't determine recipient address, skipping", M.msgid)
                continue

            if not self.processMessage(M):
                break

            # Optionally dispose of the message
            message = '%s %s' % (self.dispose, M.msgid)
            if self.pretend:
                message = message + ' (not)'
            if self.dispose:
                self.cPrint('\n', message)
            if not self.disposeMessage(M):
                continue

            self.endProcessMessage(M)
            
        self._saveCache()

class InteractiveQueue(Queue):
    """An interactive pending queue."""
    def __init__( self,
                  msgs = [],
                  cache = None,
                  command_recipient = None,
                  descending = None,
                  dispose = None,
                  older = None,
                  summary = None,
                  terse = None,
                  threshold = None,
                  verbose = 1,
                  younger = None,
                  pretend = None ):

        Queue.__init__(self,
                       msgs,
                       cache,
                       command_recipient,
                       descending,
                       dispose,
                       older,
                       summary,
                       terse,
                       threshold,
                       verbose,
                       younger,
                       pretend)


    def checkDelivered(self, M):
        if M.wasDelivered():
            return 1
        return 0

    def processMessage(self, M):
        self.showMessage(M)
        if not self.userInput(M):
            return 0
        return 1

    def userInput(self, M):
        """Get the user input."""
        try:
            message = '([p]ass / [s]how / [r]el / [d]el'
            if Defaults.PENDING_WHITELIST_APPEND:
                message = message + ' / [w]hite'
            if Defaults.PENDING_BLACKLIST_APPEND:
                message = message + ' / [b]lack'
            message = message + ' / [q]uit) [%s]: '
            inp = raw_input(message % self.dispose_def)
            ans = inp[0:1].lower()
            if ans == "":
                self.dispose = self.dispose_def
            elif ans == "p":
                self.dispose = 'pass'
            elif ans == "s":
                self.dispose = 'show'
            elif ans == "r":
                self.dispose = 'release'
            elif ans == 'd':
                self.dispose = 'delete'
            elif ans == 'w':
                self.dispose = 'whitelist'
            elif ans == 'b':
                self.dispose = 'blacklist'
            elif ans == "q":
                return 0
            else:
                self.Print('\n', "I don't understand %s" % (`inp`))
                self.dispose = 'pass'
        except KeyboardInterrupt:
            self.Print()
            return 0
        return 1

    def endProcessMessage(self, M):
        if not self.pretend:
            if self.dispose in ('show', 'whitelist', 'blacklist'):
                self.count = self.count - 1
                self.msgs.insert(self.msgs.index(M.msgid), M.msgid)
                self._delCache(M.msgid)
    



class Message:
    """A simple pending message class"""
    msg_size = 0
    bytes = 'bytes'
    confirm_accept_address = None
    def __init__(self, msgid, recipient = None):
        self.msgid = msgid
        self.msgfile = os.path.join(Defaults.DATADIR, 'pending', self.msgid)
        if not os.path.exists(self.msgfile):
            raise MessageError, MessageError('%s not found!' % self.msgid)

        self.msgobj = email.message_from_file(open(self.msgfile, 'r'))
        self.return_path = email.Utils.parseaddr(
                                        self.msgobj.get('return-path'))[1]
        if not recipient:
            self.recipient = self.msgobj.get('x-tmda-recipient')
        else:
            self.recipient = recipient

    def release(self):
        """Release a message from the pending queue."""
        import Cookie
        if Defaults.PENDING_RELEASE_APPEND:
            Util.append_to_file(self.return_path,
                                Defaults.PENDING_RELEASE_APPEND)
        timestamp, pid, suffix = self.msgid.split('.')
        # Remove Return-Path: to avoid duplicates.
        del self.msgobj['return-path']
        # Remove X-TMDA-Recipient:
        del self.msgobj['x-tmda-recipient']
        # To avoid a mail loop on re-injection, prepend an ``Old-'' prefix
        # to all existing Delivered-To lines.
        Util.rename_headers(self.msgobj, 'Delivered-To', 'Old-Delivered-To')
        # Add an X-TMDA-Confirm-Done: field to the top of the header for
        # later verification.  This includes a timestamp, pid, and HMAC.
        del self.msgobj['X-TMDA-Confirm-Done']
        self.msgobj['X-TMDA-Confirm-Done'] = Cookie.make_confirm_cookie(timestamp,
                                                                   pid, 'done')
        # Add the date when confirmed in a header.
        del self.msgobj['X-TMDA-Released']
        self.msgobj['X-TMDA-Released'] = Util.unixdate()
        # Reinject the message to the original envelope recipient.
        Util.sendmail(self.msgobj.as_string(), self.recipient, self.return_path)

    def delete(self):
        """Delete a message from the pending queue."""
        if Defaults.PENDING_DELETE_APPEND:
            Util.append_to_file(self.return_path,
                                Defaults.PENDING_DELETE_APPEND)
        os.unlink(self.msgfile)

    def whitelist(self):
        """Whitelist the message sender."""
        if Defaults.PENDING_WHITELIST_APPEND:
            Util.append_to_file(self.return_path,
                                Defaults.PENDING_WHITELIST_APPEND)
        else:
            raise Errors.ConfigError, \
                  'PENDING_WHITELIST_APPEND not defined!'

    def blacklist(self):
        """Blacklist the message sender."""
        if Defaults.PENDING_BLACKLIST_APPEND:
            Util.append_to_file(self.return_path,
                                Defaults.PENDING_BLACKLIST_APPEND)
        else:
            raise Errors.ConfigError, \
                  'PENDING_BLACKLIST_APPEND not defined!'

    def pager(self):
        Util.pager(self.msgfile)
        return ''

    def show(self):
        """Return the string representation of a message."""
        return self.msgobj.as_string()

    def getDate(self):
        timestamp = self.msgid.split('.')[0]
        return Util.unixdate(int(timestamp))

    def terse(self, date=0):
        """Return terse header information."""
        terse_hdrs = []
        for hdr in Defaults.TERSE_SUMMARY_HEADERS:
            if hdr in ('from_name', 'from_address'):
                from_name, from_address = email.Utils.parseaddr(
                                                self.msgobj.get('from'))
                if hdr == 'from_name':
                    terse_hdrs.append(from_name
                                      or from_address or 'None')
                elif hdr == 'from_address':
                    terse_hdrs.append(from_address or 'None')
            else:
                terse_hdrs.append(self.msgobj.get(hdr))

        if date:
            terse_hdrs.insert(0,self.getDate())
        else:
            terse_hdrs.insert(0, self.msgid)
        return [Util.decode_header(hdr) for hdr in terse_hdrs]
        
    def getConfirmAddress(self):
        if not self.confirm_accept_address:
            if self.recipient:
                import Cookie
                (timestamp, pid, suffix) = self.msgid.split('.')
                self.confirm_accept_address =   Cookie.make_confirm_address(
                                                self.recipient, timestamp, pid,
                                                'accept')
            else:
                return None
        return self.confirm_accept_address

    def summary(self, count = 0, total = 0, mailto = 0):
        """Return summary header information."""
        if not self.msg_size:
            self.msg_size = len(self.msgobj.as_string())
            if  self.msg_size == 1:
                self.bytes =    self.bytes[:-1]
        str = self.msgid + " ("
        if total:
            str += "%s of %s / " % (count, total)
        str += "%s %s)\n" % (self.msg_size, self.bytes)

        for hdr in Defaults.SUMMARY_HEADERS:
            str += "%s %s: %s\n" % ('  >>',
                                 hdr.capitalize()[:4].rjust(4),
                                 Util.decode_header(self.msgobj.get(hdr)))

        if mailto and self.getConfirmAddress():
            str+= '<mailto:%s>' % self.confirm_accept_address
        return str

    def wasDelivered(self):
        """Check if the message has already been delivered, and how."""
        if self.msgid.endswith(',R') or self.msgid.endswith(',C'):
            return self.msgid[-1]
        else:
            return None

