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

"""TMDA configuration variable defaults."""


# NEVER make configuration changes to this file.  ALWAYS make them in
# /etc/tmdarc or ~/.tmdarc instead.  Settings in ~/.tmdarc override
# those in /etc/tmdarc.


import binascii
import os
import stat
import string
import sys

import Errors


##############################
# General system-wide defaults
##############################

# The current process id of the Python interpreter as a string.
PID = str(os.getpid())

# General exit status codes which should be understood by all MTAs.
# Defined so we can raise exit codes within TMDA modules without
# having to create an MTA instance.
EX_OK = 0                               
EX_TEMPFAIL = 75

# TMDA parent directory.
progpath = os.path.abspath(sys.argv[0])
if os.path.islink(progpath):
    progdir = os.path.dirname(progpath)
    linkpath = os.readlink(progpath)
    if os.path.isabs(linkpath):
        progpath = linkpath
    else:
        progpath = os.path.normpath(progdir + '/' + linkpath)
PARENTDIR = os.path.split(os.path.dirname(progpath))[0] # '../'

# If the file /etc/tmdarc exists, read it before ~/.tmdarc.
# Make site-wide configuration changes to this file.
GLOBAL_TMDARC = '/etc/tmdarc'
if os.path.isfile(GLOBAL_TMDARC):
    try:
        execfile(GLOBAL_TMDARC)
    except:
        pass                            # just skip it if there is a problem
        
# Look for the user-config-file in the environment first then default
# to ~/.tmdarc or ~/.tmda/config
TMDARC = os.environ.get('TMDARC')
if not TMDARC:
    TMDARC = os.path.expanduser('~/.tmdarc')
    if not os.path.isfile(TMDARC):
        TMDARC = os.path.expanduser('~/.tmda/config')

# Read-in the user's configuration file.
if os.path.exists(TMDARC):
    execfile(TMDARC)
else:
    raise Errors.ConfigError, "Can't open configuration file: " + TMDARC

# Check for proper file permissions before proceeding.
statinfo = os.stat(TMDARC)
permbits = stat.S_IMODE(statinfo[stat.ST_MODE])
mode = int(oct(permbits))

# ALLOW_MODE_640
# Set this variable to 1 if you want to allow mode 640 .tmdarc files.
# Default is 0 (turned off)
if not vars().has_key('ALLOW_MODE_640'):
    ALLOW_MODE_640 = 0

if ALLOW_MODE_640 and mode in (400, 600, 640):
    pass
elif mode not in (400, 600):
    raise Errors.ConfigError, TMDARC + " must be chmod 400 or 600!"


import Util
import Version

TMDA_HOMEPAGE = "(http://tmda.sf.net/)"
TMDA_VERSION = Version.TMDA

############################
# User configurable settings
############################

# Only compute defaults for unset variables to speed startup.

# DATADIR
# Top-level directory which TMDA uses to store its files and
# directories.  TMDA should be free to create files and directories
# under DATADIR if need be.  Make sure to include a trailing "/".
# Default is ~/.tmda/
if not vars().has_key('DATADIR'):
    DATADIR = os.path.expanduser("~/.tmda/")

# MAIL_TRANSFER_AGENT
# Defines which mail transfer agent (MTA) software you are running.
# Possible choices are "exim", "postfix", "qmail", or "sendmail".
# Default is qmail
if not vars().has_key('MAIL_TRANSFER_AGENT'):
    MAIL_TRANSFER_AGENT = "qmail"

# DELIVERY
# The default delivery instruction for successful messages, or TMDA's
# final delivery location.  Only required if you are NOT running
# qmail.  The default value for qmail users is "_qok_" which means
# exit(0) and proceed to the next instruction in the dot-qmail file.
#
# Delivery to qmail-style Maildirs, mboxrd-format mboxes, programs
# (pipe), and forward to an e-mail addresses are supported.
#
# Acceptable syntax and restrictions for delivery instructions are
# discussed in the ``action'' section of the TMDA Filter Specification
# (config-filter.html).  Please read this documentation.
#
# Examples:
# DELIVERY = "~/Maildir/"
# DELIVERY = "~/Mailbox"
# DELIVERY = "/var/mail/jasonrm"
# DELIVERY = "|/usr/bin/maildrop"
# DELIVERY = "|/usr/bin/procmail ~/.procmailrc-tmda"
# DELIVERY = "me@new.job.com"
#
# No default for non-qmail users.
if not vars().has_key('DELIVERY'):
    if MAIL_TRANSFER_AGENT == 'qmail':
        DELIVERY = "_qok_"
    else:
        raise Errors.ConfigError, \
              "non-qmail users must define DELIVERY in " + TMDARC

# RECIPIENT_DELIMITER
# A single character which specifies the separator between user names
# and address extensions (e.g, user-ext).
# The default under qmail is `-', while the default for Sendmail and
# friends is likely `+'.
# Default is "-"
if not vars().has_key('RECIPIENT_DELIMITER'):
    RECIPIENT_DELIMITER = "-"

# SENDMAIL
# The path to the sendmail program, or sendmail compatibility
# interface.  Defaults to one of the two standard locations, but you
# can override it in case it is installed elsewhere.
if not vars().has_key('SENDMAIL'):
    for sendmail in ('/usr/sbin/sendmail', '/usr/lib/sendmail'):
        if os.path.exists(sendmail):
            SENDMAIL = sendmail
            break

# USEVIRTUALDOMAINS
# Set this variable to 0 if want to turn off TMDA's qmail virtualdomains
# support.  This should obviously only be done if you are not running
# any qmail virtualdomains, but it will improve performance.
# Default is 1 (turned on)
if not vars().has_key('USEVIRTUALDOMAINS'):
    USEVIRTUALDOMAINS = 1

# VIRTUALDOMAINS
# virtualdomains defaults to /var/qmail/control/virtualdomains, but
# this lets you override it in case it is installed elsewhere.  Used
# for virtualdomain processing in tmda-filter.
if not vars().has_key('VIRTUALDOMAINS'):
    VIRTUALDOMAINS = "/var/qmail/control/virtualdomains"

# BOUNCE_ENV_SENDER
# The envelope sender of the bounce message.
#
# Example:
# BOUNCE_ENV_SENDER = "devnull@domain.dom"
#
# Default is an empty envelope sender <>.
if not vars().has_key('BOUNCE_ENV_SENDER'):
    # Exim and Sendmail don't like -f ''
    if MAIL_TRANSFER_AGENT in ('exim', 'sendmail'):
        BOUNCE_ENV_SENDER = '<>'
    else:
        BOUNCE_ENV_SENDER = ''

# BOUNCE_TEXT_FILTER_INCOMING
# Text for the failure notice returned to the sender when a 'bounce'
# or 'reject' rule is matched in the incoming filter file.  Set to
# None to disable notification.
if not vars().has_key('BOUNCE_TEXT_FILTER_INCOMING'):
    BOUNCE_TEXT_FILTER_INCOMING = """Message rejected by recipient."""

# BOUNCE_TEXT_INVALID_CONFIRMATION
# Text for the failure notice returned to the sender when a message is
# sent to an invalid confirmation address.  Set to None to disable
# notification.
if not vars().has_key('BOUNCE_TEXT_INVALID_CONFIRMATION'):
    BOUNCE_TEXT_INVALID_CONFIRMATION = """This confirmation address is invalid."""

# BOUNCE_TEXT_NONEXISTENT_PENDING
# Text for the failure notice returned to the sender when a
# confirmation response arrives for a message which could not be
# located.  Set to None to disable notification.
if not vars().has_key('BOUNCE_TEXT_NONEXISTENT_PENDING'):
    BOUNCE_TEXT_NONEXISTENT_PENDING = """Your original message could not be located."""
        
# BARE_APPEND
# Filename to which a recipient's e-mail address should be
# automatically appended if the outgoing <action> is in the form
# 'bare=append'.
#
# Example:
# BARE_APPEND = "/full/path/to/whitelist"
#
# No default
if not vars().has_key('BARE_APPEND'):
    BARE_APPEND = None

# CONFIRM_ADDRESS
# An optional e-mail address to use for creating confirmation
# addresses.  Normally, the recipient address is used, but in some
# virtual domain or forwarding scenarios, you may wish to have
# confirmation address be based on a fixed address regardless of the
# recipient address.
#
# Example:
# CONFIRM_ADDRESS = "webmaster@domain.dom"
#
# No default
if not vars().has_key('CONFIRM_ADDRESS'):
    CONFIRM_ADDRESS = None

# CONFIRM_APPEND
# Filename to which a sender's e-mail address should be automatically
# appended once they confirm a message.  This can be used to implement
# "auto-whitelisting" functionality.
#
# Example:
# CONFIRM_APPEND = "/full/path/to/whitelist"
#
# No default
if not vars().has_key('CONFIRM_APPEND'):
    CONFIRM_APPEND = None
    
# CONFIRM_CC
# An optional e-mail address which will be sent a copy of any message
# that triggers a confirmation request.
#
# Example:
# CONFIRM_CC = "jdoe-confirms@domain.dom"
#
# No default.
if not vars().has_key('CONFIRM_CC'):
    CONFIRM_CC = None

# CONFIRM_ACCEPT_NOTIFY
# Set this variable to 0 if you do not want to generate any confirmation
# acceptance notices.
# Default is 1 (turned on)
if not vars().has_key('CONFIRM_ACCEPT_NOTIFY'):
    CONFIRM_ACCEPT_NOTIFY = 1

# CONFIRM_ACCEPT_TEXT_INITIAL
# Text for the confirmation acceptance notice returned to the sender
# when they initially confirm their original message causing it to
# be delivered.  Set to None to disable notification.
if not vars().has_key('CONFIRM_ACCEPT_TEXT_INITIAL'):
    CONFIRM_ACCEPT_TEXT_INITIAL = \
"""Your confirmation was accepted,
and so your original message has been delivered."""

# CONFIRM_ACCEPT_TEXT_ALREADY_CONFIRMED
# Text for the confirmation acceptance notice returned to the sender
# when they successfully confirm a message which has already been
# confirmed.  Set to None to disable notification.
if not vars().has_key('CONFIRM_ACCEPT_TEXT_ALREADY_CONFIRMED'):
    CONFIRM_ACCEPT_TEXT_ALREADY_CONFIRMED = \
"""Your original message has already been confirmed and delivered;
you don't need to confirm it again."""

# CONFIRM_ACCEPT_TEXT_ALREADY_RELEASED
# Text for the confirmation acceptance notice returned to the sender
# when they successfully confirm a message which has already been
# manually released with tmda-pending.  Set to None to disable
# notification.
if not vars().has_key('CONFIRM_ACCEPT_TEXT_ALREADY_RELEASED'):
    CONFIRM_ACCEPT_TEXT_ALREADY_RELEASED = \
"""Your original message has already been released and delivered."""
    
# CONFIRM_ACCEPT_CC
# An optional e-mail address which will be sent a copy of the
# confirmation acceptance messages people send you.
#
# Example:
# CONFIRM_ACCEPT_CC = "jdoe-confirm-replies@domain.dom"
#
# No default.
if not vars().has_key('CONFIRM_ACCEPT_CC'):
    CONFIRM_ACCEPT_CC = None

# CONFIRM_MAX_MESSAGE_SIZE
# This is the largest size (in bytes) that a message can be before the
# its body is excluded from the confirmation request/acceptance
# notice.  Set this to None to allow any size message.
# Default is 50000
if not vars().has_key('CONFIRM_MAX_MESSAGE_SIZE'):
    CONFIRM_MAX_MESSAGE_SIZE = 50000

# TEMPLATE_DIR
# Full path to a directory containing custom TMDA templates.  Any
# templates found in this directory will be used, otherwise the
# default templates will be used.
#
# Example:
# TEMPLATE_DIR = "/full/path/to/templates/"
#
# No default.
if not vars().has_key('TEMPLATE_DIR'):
    TEMPLATE_DIR = None

# DATED_TEMPLATE_VARS
# Set this variable to 1 if you want to use 'dated' address variables
# in your templates.
# Default is 0 (turned off)
if not vars().has_key('DATED_TEMPLATE_VARS'):
    DATED_TEMPLATE_VARS = 0

# SENDER_TEMPLATE_VARS
# Set this variable to 1 if you want to use 'sender' address variables
# in your templates.
# Default is 0 (turned off)
if not vars().has_key('SENDER_TEMPLATE_VARS'):
    SENDER_TEMPLATE_VARS = 0

# CRYPT_KEY
# Your encryption key should be unique and kept secret.
# Use the included "tmda-keygen" program to generate your key.
# No default.
if not vars().has_key('CRYPT_KEY'):
    raise Errors.ConfigError, "CRYPT_KEY not defined in " + TMDARC
else:
    # Convert key from hex back into raw binary.
    # Hex has only 4 bits of entropy per byte as opposed to 8.
    CRYPT_KEY = binascii.unhexlify(CRYPT_KEY)
    
# FILTER_INCOMING
# Filter file which controls how incoming messages are tagged.
# Look for the filter-file in the environment first.
# Default is ~/.tmda/filters/incoming
env_FILTER_INCOMING = os.environ.get('TMDA_FILTER_INCOMING')
if env_FILTER_INCOMING:
    FILTER_INCOMING = env_FILTER_INCOMING
elif not vars().has_key('FILTER_INCOMING'):
    FILTER_INCOMING = os.path.join(DATADIR, 'filters', 'incoming')

# FILTER_OUTGOING
# Filter file which controls how outgoing messages are tagged.
# Look for the filter-file in the environment first.
# Default is ~/.tmda/filters/outgoing
env_FILTER_OUTGOING = os.environ.get('TMDA_FILTER_OUTGOING')
if env_FILTER_OUTGOING:
    FILTER_OUTGOING = env_FILTER_OUTGOING
elif not vars().has_key('FILTER_OUTGOING'):
    FILTER_OUTGOING = os.path.join(DATADIR, 'filters', 'outgoing')
    
# FILTER_BOUNCE_CC
# An optional e-mail address which will be sent a copy of any message
# that bounces because of a match in FILTER_INCOMING.
#
# Example:
# FILTER_BOUNCE_CC = "jdoe-bounces@domain.dom"
#
# No default.
if not vars().has_key('FILTER_BOUNCE_CC'):
    FILTER_BOUNCE_CC = None

# FILTER_DROP_CC
# An optional e-mail address which will be sent a copy of any message
# that is dropped because of a match in FILTER_INCOMING.
#
# Example:
# FILTER_DROP_CC = "jdoe-drops@domain.dom"
#
# No default.
if not vars().has_key('FILTER_DROP_CC'):
    FILTER_DROP_CC = None

# ACTION_INCOMING
# Specifies how incoming messages should be disposed of by default if
# they didn't match FILTER_INCOMING and were not sent to a tagged
# address.
# Possible values include:
#
# "bounce"
#    bounce the message
#
# "drop"
#    silently drop the message
#
# "ok"
#    deliver the message
#
# "confirm"
#    request confirmation for the message
#
# Default is confirm
if not vars().has_key('ACTION_INCOMING'):
    ACTION_INCOMING = "confirm"

# ACTION_OUTGOING
# Specifies how outgoing messages should be tagged by default if there
# are no matches in FILTER_OUTGOING and no X-TMDA header.
# Possible values include:
#
# "bare[=append]"
#    don't tag
#
# "dated[=timeout_interval]"
#    tag with a dated address
#
# "sender[=sender_address]"
#    tag with a sender address
#
# "exp=full_address"
#    tag with explicit address
#
# "kw=keyword"
#    tag with a keyword address
#
# Default is dated
if not vars().has_key('ACTION_OUTGOING'):
    ACTION_OUTGOING = "dated"

# FINGERPRINT
#
# A list containing one or more message headers whose values should be
# used to create a "fingerprint" for the message.  If the header value
# is 'body' (all-lowercase), the message body content is used instead
# of a header value.  The fingerprint is a SHA-1 HMAC digest
# represented as a base64-encoded string.  This fingerprint will be
# added to your outgoing client-side messages (i.e, messages sent with
# tmda-sendmail) in an `X-TMDA-Fingerprint' header prior to injection.
#
# Examples:
#
# FINGERPRINT = ["message-id"]
# FINGERPRINT = ["message-id", "from", "date"]
# FINGERPRINT = ["message-id", "body"]
#
# Things to keep in mind, especially if verifying these fingerprints
# with non-TMDA code.
#
# * CRYPT_KEY is converted from hex into raw binary before it is
#   used to create the HMAC object.
# * The order of header names in the FINGERPRINT list is important;
#   updates are made in the order listed.
# * If a listed header doesn't exist in the message, no update attempt
#   will be made for that header.
# * For a listed header, only the header value (i.e, text after the
#   colon) is used.  Additionally, leading and trailing whitespace (but
#   not internal whitespace) is stripped from that value.
#
# For example, if the listed headers consisted of:
#
# Message-ID: <20011212192455.A7060@nightshade.la.mastaler.com>
# From: "Jason R. Mastaler" <jason-dated-1008901496.5356ec@mastaler.com>
# Date: Wed, 12 Dec 2001 19:24:55 -0700
#
# The strings which are used to create the HMAC digest are the
# following (in order):
#
# <20011212192455.A7060@nightshade.la.mastaler.com>
# "Jason R. Mastaler" <jason-dated-1008901496.5356ec@mastaler.com>
# Wed, 12 Dec 2001 19:24:55 -0700
#
# The following header would then be added to the outgoing message:
# X-TMDA-Fingerprint: vDBoOHtIUE6VniJguxJ+w2fR5bU
#
# No default
if not vars().has_key('FINGERPRINT'):
    FINGERPRINT = None
    
# FULLNAME
# Your full name.
#
# Example:
# FULLNAME = "John Doe"
#
# Default comes from your environment or the password file.
if not vars().has_key('FULLNAME'):
    FULLNAME = Util.getfullname()

# HMAC_BYTES
# An integer which determines the length of the HMACs used in TMDA's
# "cookies".  Read the `CRYPTO' file for more information.  Changing
# this value will will invalidate all previously generated HMACs.
# Default is 3 (24-bit HMACs)
if not vars().has_key('HMAC_BYTES'):
    HMAC_BYTES = 3

# HOSTNAME
# The right-hand side of your email address (after `@').  Used only in
# cases where TMDA can't determine this itself.
#
# Example:
# HOSTNAME = "domain.dom"
#
# Defaults to the fully qualified domain name of the localhost.
if not vars().has_key('HOSTNAME'):
    HOSTNAME = Util.gethostname()
    
# LOGFILE_DEBUG
# Filename which uncaught exceptions should be written to.
#
# Example:
# LOGFILE_DEBUG = "/path/to/tmda_debug.log"
#
# No default.
if not vars().has_key('LOGFILE_DEBUG'):
    LOGFILE_DEBUG = None
    
# LOGFILE_INCOMING
# Filename which delivery summaries should be written to.
#
# Example:
# LOGFILE_INCOMING = "/path/to/tmda_incoming.log"
#
# No default.
if not vars().has_key('LOGFILE_INCOMING'):
    LOGFILE_INCOMING = None

# LOCALDATE
# Set this variable to 0 if you want TMDA to generate ``Date:''
# headers in UTC instead of the local time zone.
# Default is 1 (use local time zone)
if not vars().has_key('LOCALDATE'):
    LOCALDATE = 1

# MESSAGE_FROM_STYLE
# Specifies how `From' headers should look when tagging outgoing
# messages with tmda-sendmail.  There are two valid values:
#
#     "address"
#           Just the address - king@grassland.com
#
#     "angles"
#           Elvis Parsley <king@grassland.com>
#
# Default is "angles".
if not vars().has_key('MESSAGE_FROM_STYLE'):
    MESSAGE_FROM_STYLE = "angles"

# DELIVERED_CACHE
# Path to the cache file used to keep track of which messages have
# already been delivered.
#
# Default is ~/.tmda/pending/.delivered_cache
if not vars().has_key('DELIVERED_CACHE'):
    DELIVERED_CACHE = os.path.join(DATADIR, 'pending', '.delivered_cache')

# DELIVERED_CACHE_LEN
#
# An integer which specifies the maximum number of entries held by
# DELIVERED_CACHE.
#
# Make sure this value is larger than the number of messages normally
# stored in your pending queue.  The default value may not suffice if
# you run a very high traffic TMDA, and/or have a long pending queue
# purge interval.
#
# Default is 5000
if not vars().has_key('DELIVERED_CACHE_LEN'):
    DELIVERED_CACHE_LEN = 5000

# PENDING_CACHE
# Path to the cache file used when tmda-pending is invoked with the
# --cache option.
#
# Default is ~/.tmda/pending/.msgcache
if not vars().has_key('PENDING_CACHE'):
    PENDING_CACHE = os.path.join(DATADIR, 'pending', '.msgcache')
    
# PENDING_CACHE_LEN
# An integer which specifies the maximum number of entries held by
# PENDING_CACHE.  Make sure this is greater than the number of
# messages kept in your pending queue, or else you'll start seeing
# previously viewed messages again.
#
# Default is 5000
if not vars().has_key('PENDING_CACHE_LEN'):
    PENDING_CACHE_LEN = 5000

# PENDING_DELETE_APPEND
# Filename to which a sender's e-mail address should be automatically
# appended when a message is "deleted" by tmda-pending.
#
# Example:
# PENDING_DELETE_APPEND = "/full/path/to/blacklist"
#
# No default
if not vars().has_key('PENDING_DELETE_APPEND'):
    PENDING_DELETE_APPEND = None

# PENDING_RELEASE_APPEND
# Filename to which a sender's e-mail address should be automatically
# appended when a message is "released" by tmda-pending.
#
# Example:
# PENDING_RELEASE_APPEND = "/full/path/to/whitelist"
#
# No default
if not vars().has_key('PENDING_RELEASE_APPEND'):
    PENDING_RELEASE_APPEND = None

# PURGED_HEADERS
# A list containing one or more message headers that should be removed
# from outgoing client-side messages (i.e, messages sent with
# tmda-sendmail) prior to injection.  Listed headers are
# case-insensitive, and the purging will only be attempted if the
# header actually exists.
#
# Examples:
#
# PURGED_HEADERS = ["x-mailer"]
# PURGED_HEADERS = ["x-mailer", "user-agent"]
#
# No default
if not vars().has_key('PURGED_HEADERS'):
    PURGED_HEADERS = None

# RECIPIENT_HEADER
# A string containing the name of a header (case-insensitive) whose
# contents will be taken as the envelope recipient of the message.
# The header should contain one fully-qualified e-mail address.  This
# can be used in rare cases when you need to override the RECIPIENT
# environment variable, which is how TMDA normally determines the
# envelope recipient address.
#
# Example:
#
# RECIPIENT_HEADER = 'x-originally-to'
#
# Then, if the message contains the following header:
#
# X-Originally-To: webmaster@domain.dom
#
# TMDA will take webmaster@domain.dom as the envelope recipient of the
# message rather than the value of RECIPIENT.
#
# WARNING: If you enable this feature, make sure that the method you
# are using to add the header will overwrite or replace an existing
# header of the same name (such as reformail/formail's -i and -I
# options do).  Otherwise the envelope recipient will be invalid which
# will break the confirmation process.
#
# No default
if not vars().has_key('RECIPIENT_HEADER'):
    RECIPIENT_HEADER = None

# TERSE_SUMMARY_HEADERS
# A list containing one or more message headers that should be
# displayed by tmda-pending's `--terse option'.  Listed headers are
# case-insensitive.  'from_name' and 'from_address' can be used to
# specify the Fullname and e-mail address from the message's "From:"
# header.
#
# Examples:
#
# TERSE_SUMMARY_HEADERS = ["return-path"]
# TERSE_SUMMARY_HEADERS = ["from_name", "from_address", "subject"]
#
# Default is the Fullname followed by Subject.
if not vars().has_key('TERSE_SUMMARY_HEADERS'):
    TERSE_SUMMARY_HEADERS = ['from_name', 'subject']

# TIMEOUT
# The timeout interval for 'dated' addresses.  The available units are
# (Y=years, M=months, w=weeks, d=days, h=hours, m=minutes, s=seconds).
# Default is 5d (5 days).
if not vars().has_key('TIMEOUT'):
    TIMEOUT = "5d"

# USERNAME
# The left-hand side of your e-mail address (before `@').
#
# Example:
# USERNAME = "jdoe"
#
# Defaults to your UNIX username.
if not vars().has_key('USERNAME'):
    USERNAME = Util.getusername()
    
###################################
# END of user configurable settings
###################################
