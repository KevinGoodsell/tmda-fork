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

"""TMDA configuration variable defaults.

See http://tmda.net/config-vars.html for an HTMLized version of the
information below.
"""


# NEVER make configuration changes to this file.  ALWAYS make them in
# /etc/tmdarc or ~/.tmda/config instead.

import binascii
import os
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

# If the file /etc/tmdarc exists, read it before ~/.tmda/config.
# Make site-wide configuration changes to this file.
GLOBAL_TMDARC = '/etc/tmdarc'
if os.path.exists(GLOBAL_TMDARC):
    try:
        execfile(GLOBAL_TMDARC)
    except:
        pass                            # just skip it if there is a problem
        
# Look for the user-config-file in the environment first then default
# to ~/.tmdarc or ~/.tmda/config
TMDARC = os.environ.get('TMDARC')
if not TMDARC:
    TMDARC = os.path.expanduser('~/.tmdarc')
    if not os.path.exists(TMDARC):
        TMDARC = os.path.expanduser('~/.tmda/config')

# CONFIG_EXEC
# If set to 0 in GLOBAL_TMDARC, the user's TMDARC file will be parsed
# using ConfigParser, otherwise it will evaluated as a sequence of
# Python statements using execfile().
# Default is 1 (execfile())
if not vars().has_key('CONFIG_EXEC'):
    CONFIG_EXEC = 1

# Read-in the user's configuration file.
if os.path.exists(TMDARC):
    if CONFIG_EXEC:
        execfile(TMDARC)
    else:
        import ConfigParser
        cf = ConfigParser.ConfigParser()
        cf.read(TMDARC)
        cf_section = 'TMDA_CONFIG'
        for option in cf.options(cf_section):
            value = cf.get(cf_section, option)
            option = option.upper()
            # Translate options into variables.
            if value in list(string.digits):
                # make sure integer values don't get turned into strings
                exec('%s = %s' % (option, value))
            else:
                exec('%s = "%s"' % (option, value))


import Util
import Version

TMDA_HOMEPAGE = "(http://tmda.net/)"
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
#
# Default is "-"
if not vars().has_key('RECIPIENT_DELIMITER'):
    RECIPIENT_DELIMITER = "-"

# ALLOW_MODE_640
# Set this variable to 1 if you want to allow a mode 640 CRYPT_KEY_FILE.
# Default is 0 (turned off)
if not vars().has_key('ALLOW_MODE_640'):
    ALLOW_MODE_640 = 0

# CRYPT_KEY_FILE
# File which contains your unique TMDA secret key generated by the
# `tmda-keygen' program.  The key should be unquoted in the file.
# This file must be chmod 400 or 600, unless ALLOW_MODE_640 is on.
# Default is ~/.tmda/crypt_key
if not vars().has_key('CRYPT_KEY_FILE'):
    CRYPT_KEY_FILE = os.path.join(DATADIR, 'crypt_key')
if os.path.exists(CRYPT_KEY_FILE):
    crypt_key_filemode = Util.getfilemode(CRYPT_KEY_FILE)
    if crypt_key_filemode not in (400, 600):
        if ALLOW_MODE_640 and crypt_key_filemode == 640:
            pass
        else:
            raise Errors.ConfigError, \
                  CRYPT_KEY_FILE + " must be chmod 400 or 600!"
else:
    raise Errors.ConfigError, "Can't find key file: " + CRYPT_KEY_FILE

# Read key from CRYPT_KEY_FILE, and then convert it from hex back into
# raw binary.  Hex has only 4 bits of entropy per byte as opposed to 8.
CRYPT_KEY = binascii.unhexlify(open(CRYPT_KEY_FILE).read().strip())

# OUTGOINGMAIL
# Final delivery method for all outgoing mail (server and client).
# Possible values include:
# 
# "smtp"
#    Deliver messages by handing them off to an SMTP server (i.e,
#    smarthost).  Be sure that the "SMTPHOST" variable (see below) is
#    set correctly.
#
# "sendmail"
#    Deliver messages via the command line interface to the sendmail
#    program (/usr/sbin/sendmail).  Use at your own risk.  "smtp" is
#    highly recommended.
#
#    SECURITY WARNING: The 'sendmail' method is not secure.  Because
#    this method uses popen(), it goes through the shell.  It does not
#    scan the arguments for potential exploits and so it should be
#    considered unsafe.  For performance reasons, it's not recommended
#    either -- use the 'smtp' method instead, even if
#    MAIL_TRANSFER_AGENT is "sendmail".
#
# Default is "smtp"
if not vars().has_key('OUTGOINGMAIL'):
    OUTGOINGMAIL = "smtp"

# SMTPHOST
# SMTP host and optional port, when OUTGOINGMAIL is "smtp".
# If the hostname or IP address ends with a colon (":") followed by a
# number, that suffix will be stripped off and the number interpreted
# as the port number to use.  Otherwise, the standard SMTP port (25)
# will be used.
#
# Examples:
#
# SMTPHOST = "localhost"
# SMTPHOST = "172.16.78.20:2525"
# SMTPHOST = "mailhost.company.com"
# SMTPHOST = "mailhost.company.com:1234"
#
# Default is "localhost" (port 25 on the local host)
if not vars().has_key('SMTPHOST') and OUTGOINGMAIL == 'smtp':
    SMTPHOST = "localhost"

# SMTPAUTH_USERNAME
# The username to authenticate with if your SMTP server requires
# authentication.  You must also define SMTPAUTH_PASSWORD if you use
# this option.  Requires Python 2.2 or greater.
#
# Examples:
#
# SMTPAUTH_USERNAME = "johndoe"
#
# No default.
if not vars().has_key('SMTPAUTH_USERNAME') and OUTGOINGMAIL == 'smtp':
    SMTPAUTH_USERNAME = None

# SMTPAUTH_PASSWORD
# The password to authenticate with if your SMTP server requires
# authentication.  You must also define SMTPAUTH_USERNAME if you use
# this option.  Requires Python 2.2 or greater.
#
# Examples:
#
# SMTPAUTH_PASSWORD = "6Yu_9iKzs"
#
# No default.
if not vars().has_key('SMTPAUTH_PASSWORD') and OUTGOINGMAIL == 'smtp':
    SMTPAUTH_PASSWORD = None

# SMTPSSL
# Set this variable to 1 to put the SMTP connection in TLS (Transport
# Layer Security) mode. All SMTP commands that follow will be
# encrypted.  Your Python's socket module must be compiled with SSL
# support.  Requires Python 2.2 or greater.
#
# Default is 0 (turned off)
if not vars().has_key('SMTPSSL') and OUTGOINGMAIL == 'smtp':
    SMTPSSL = 0

# SMTPSSL_KEYFILE
# When SMTPSSL is enabled, this is the optional name of a PEM
# formatted file that contains your private key.
#
# No default.
if not vars().has_key('SMTPSSL_KEYFILE') and \
       OUTGOINGMAIL == 'smtp' and SMTPSSL:
    SMTPSSL_KEYFILE = None

# SMTPSSL_CERTFILE
# When SMTPSSL is enabled, this is the optional name of a PEM
# formatted certificate chain file.  Warning: This does not do any
# certificate verification.
#
# No default.
if not vars().has_key('SMTPSSL_CERTFILE') and \
       OUTGOINGMAIL == 'smtp' and SMTPSSL:
    SMTPSSL_CERTFILE = None

# SMTP_MAX_SESSIONS_PER_CONNECTION
# An integer specifying a ceiling on the number of SMTP sessions to
# perform on a single socket connection, when OUTGOINGMAIL is
# "smtp".  Some MTAs have limits.  Set this to 0 to do as many
# as we like (i.e. your MTA has no limits).  Set this to some number
# great than 0 and TMDA will close the SMTP connection and re-open it
# after this number of consecutive sessions.
#
# Default is 0
if not vars().has_key('SMTP_MAX_SESSIONS_PER_CONNECTION') and \
       OUTGOINGMAIL == 'smtp':
    SMTP_MAX_SESSIONS_PER_CONNECTION = 0

# SENDMAIL_PROGRAM
# The path to the sendmail program, or sendmail compatibility
# interface when OUTGOINGMAIL is "sendmail".
# Defaults to one of the two standard locations.
if not vars().has_key('SENDMAIL_PROGRAM') and OUTGOINGMAIL == 'sendmail':
    for sendmail in ('/usr/sbin/sendmail', '/usr/lib/sendmail'):
        if os.path.exists(sendmail):
            SENDMAIL_PROGRAM = sendmail
            break

# USEVIRTUALDOMAINS
# Set this variable to 0 if want to turn off TMDA's qmail virtualdomains
# support.  This should obviously only be done if you are not running
# any qmail virtualdomains, but it will improve performance.
#
# Default is 1 (turned on)
if not vars().has_key('USEVIRTUALDOMAINS'):
    USEVIRTUALDOMAINS = 1

# VIRTUALDOMAINS
# virtualdomains defaults to /var/qmail/control/virtualdomains, but
# this lets you override it in case it is installed elsewhere.  Used
# for virtualdomain processing in tmda-filter.
#
# Default is /var/qmail/control/virtualdomains
if not vars().has_key('VIRTUALDOMAINS'):
    VIRTUALDOMAINS = "/var/qmail/control/virtualdomains"

# BOUNCE_ENV_SENDER
# The envelope sender of a bounce message.
#
# Example:
# BOUNCE_ENV_SENDER = "devnull@domain.dom"
#
# Default is an empty envelope sender <>.
if not vars().has_key('BOUNCE_ENV_SENDER'):
    if OUTGOINGMAIL == 'sendmail' and \
           MAIL_TRANSFER_AGENT in ('qmail', 'postfix'):
        # qmail/Postfix's /usr/sbin/sendmail doesn't like -f '<>'
        BOUNCE_ENV_SENDER = ''
    else:
        BOUNCE_ENV_SENDER = '<>'

# BOUNCE_TEXT_FILTER_INCOMING
# Text for the failure notice returned to the sender when a 'bounce'
# or 'reject' rule is matched in the incoming filter file.  Set to
# None to disable notification.
#
# Default is "Message rejected by recipient."
if not vars().has_key('BOUNCE_TEXT_FILTER_INCOMING'):
    BOUNCE_TEXT_FILTER_INCOMING = """Message rejected by recipient."""

# BOUNCE_TEXT_INVALID_CONFIRMATION
# Text for the failure notice returned to the sender when a message is
# sent to an invalid confirmation address.  Set to None to disable
# notification.
#
# Default is "This confirmation address is invalid."
if not vars().has_key('BOUNCE_TEXT_INVALID_CONFIRMATION'):
    BOUNCE_TEXT_INVALID_CONFIRMATION = """This confirmation address is invalid."""

# BOUNCE_TEXT_NONEXISTENT_PENDING
# Text for the failure notice returned to the sender when a
# confirmation response arrives for a message which could not be
# located.  Set to None to disable notification.
#
# Default is "Your original message could not be located."
if not vars().has_key('BOUNCE_TEXT_NONEXISTENT_PENDING'):
    BOUNCE_TEXT_NONEXISTENT_PENDING = """Your original message could not be located."""

# BOUNCE_TEXT_FAIL_DATED
# Text for the failure notice returned to the sender when a
# dated address does not verify with a correct HMAC.  Set to None 
# to disable notification.  Setting to None will cause the same behavior
# as setting ACTION_FAIL_DATED to drop
#
# Default is "You have sent email to an invalid address."
if not vars().has_key('BOUNCE_TEXT_FAIL_DATED'):
    BOUNCE_TEXT_FAIL_DATED = """You have sent email to an invalid address."""

# BOUNCE_TEXT_EXPIRED_DATED
# Text for the failure notice returned to the sender when a
# dated address is expired.  Set to None to disable notification.  Setting
# to None will cause the same behavior as setting ACTION_EXPIRED_DATED to
# drop
#
# Default is "You have sent email to an expired address."
if not vars().has_key('BOUNCE_TEXT_EXPIRED_DATED'):
    BOUNCE_TEXT_EXPIRED_DATED = """You have sent email to an expired address."""

# BOUNCE_TEXT_FAIL_SENDER
# Text for the failure notice returned to the sender when a
# sender address does not verify with a correct HMAC.  Set to None
# to disable notification.  Setting to None will cause the same behavior
# as setting ACTION_FAIL_SENDER to drop
#
# Default is "You have sent email to an address you are not authorized to use."
if not vars().has_key('BOUNCE_TEXT_FAIL_SENDER'):
    BOUNCE_TEXT_FAIL_SENDER = """You have sent email to an address you are not authorized to use."""

# BOUNCE_TEXT_FAIL_KEYWORD
# Text for the failure notice returned to the sender when a
# keyword address does not verify with a correct HMAC. Set to None
# to disable notification.  Setting to None will cause the same behavior
# as setting ACTION_FAIL_KEYWORD to drop.
#
# Default is "You have sent email to an invalid address."
if not vars().has_key('BOUNCE_TEXT_FAIL_KEYWORD'):
    BOUNCE_TEXT_FAIL_KEYWORD = """You have sent email to an invalid address."""
        
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
#
# Default is 1 (turned on)
if not vars().has_key('CONFIRM_ACCEPT_NOTIFY'):
    CONFIRM_ACCEPT_NOTIFY = 1

# CONFIRM_ACCEPT_TEXT_INITIAL
# Text for the confirmation acceptance notice returned to the sender
# when they initially confirm their original message causing it to
# be delivered.  Set to None to disable notification.
#
# Default is:
# "Your confirmation was accepted, and so your original message has been delivered."
if not vars().has_key('CONFIRM_ACCEPT_TEXT_INITIAL'):
    CONFIRM_ACCEPT_TEXT_INITIAL = \
"""Your confirmation was accepted,
and so your original message has been delivered."""

# CONFIRM_ACCEPT_TEXT_ALREADY_CONFIRMED
# Text for the confirmation acceptance notice returned to the sender
# when they successfully confirm a message which has already been
# confirmed.  Set to None to disable notification.
#
# Default is:
# "Your original message has already been confirmed and delivered; you don't need to confirm it again."
if not vars().has_key('CONFIRM_ACCEPT_TEXT_ALREADY_CONFIRMED'):
    CONFIRM_ACCEPT_TEXT_ALREADY_CONFIRMED = \
"""Your original message has already been confirmed and delivered;
you don't need to confirm it again."""

# CONFIRM_ACCEPT_TEXT_ALREADY_RELEASED
# Text for the confirmation acceptance notice returned to the sender
# when they successfully confirm a message which has already been
# manually released with tmda-pending.  Set to None to disable
# notification.
#
# Default is "Your original message has already been released and delivered."
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
#
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

# TEMPLATE_DIR_MATCH_SENDER
# Set this variable to 1 if you want to use sender specific template
# directory matching. Make sure you also have TEMPLATE_DIR set.
#
# With this feature enabled, TMDA will look for templates in a
# subdirectory of TEMPLATE_DIR that matches the sender address, and
# then increasingly general portions of the domain part of the address.
#
# For example, if mail arrives from foo@bar.baz.de, TMDA will look for
# templates in these subdirectories of TEMPLATE_DIR, in this order:
#
#  foo@bar.baz.de/
#
#  bar.baz.de/
#
#  baz.de/
#
#  de/
#
# If no sender based templates can be found, TEMPLATE_DIR itself and
# then the default locations will be tried.
#
# Default is 0 (turned off)
if not vars().has_key('TEMPLATE_DIR_MATCH_SENDER'):
    TEMPLATE_DIR_MATCH_SENDER = 0

# TEMPLATE_EMAIL_HEADERS
# A list containing the names of headers in your templates that
# contain an e-mail address.  This is necessary so that the e-mail
# address will avoid being RFC 2047 encoded when handling
# internationalized headers.
#
# Example:
# TEMPLATE_EMAIL_HEADERS = ["from", "reply-to"]
#
# Default is "From:" and "Reply-To:".
if not vars().has_key('TEMPLATE_EMAIL_HEADERS'):
    TEMPLATE_EMAIL_HEADERS = ['from', 'reply-to']

# TEMPLATE_ENCODED_HEADERS
# A list containing the names of headers in your templates that might
# contain an RFC 2047 encoded string.  This is necessary so that they
# can be decoded first when handling internationalized headers.
#
# Example:
# TEMPLATE_ENCODED_HEADERS = ["subject"]
#
# Default is "Subject:".
if not vars().has_key('TEMPLATE_ENCODED_HEADERS'):
    TEMPLATE_ENCODED_HEADERS = ['subject']

# DATED_TEMPLATE_VARS
# Set this variable to 1 if you want to use 'dated' address variables
# in your templates.
#
# Default is 0 (turned off)
if not vars().has_key('DATED_TEMPLATE_VARS'):
    DATED_TEMPLATE_VARS = 0

# SENDER_TEMPLATE_VARS
# Set this variable to 1 if you want to use 'sender' address variables
# in your templates.
#
# Default is 0 (turned off)
if not vars().has_key('SENDER_TEMPLATE_VARS'):
    SENDER_TEMPLATE_VARS = 0

# FILTER_INCOMING
# Filter file which controls how incoming messages are tagged.
# Look for the filter-file in the environment first.
#
# Default is ~/.tmda/filters/incoming
env_FILTER_INCOMING = os.environ.get('TMDA_FILTER_INCOMING')
if env_FILTER_INCOMING:
    FILTER_INCOMING = env_FILTER_INCOMING
elif not vars().has_key('FILTER_INCOMING'):
    FILTER_INCOMING = os.path.join(DATADIR, 'filters', 'incoming')

# FILTER_OUTGOING
# Filter file which controls how outgoing messages are tagged.
# Look for the filter-file in the environment first.
#
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
# "hold"
#    silently hold message in pending queue
#
# Default is confirm
if not vars().has_key('ACTION_INCOMING'):
    ACTION_INCOMING = "confirm"

# ACTION_FAIL_DATED
# Specifies how incoming messages should be disposed of if they are sent
# to a dated address that does not properly verify.  
# Possible values include:
#
# "bounce"
#    bounce the message - uses BOUNCE_TEXT_FAIL_DATED
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
# "hold"
#    silently hold message in pending queue
#
# Default is confirm
if not vars().has_key('ACTION_FAIL_DATED'):
    ACTION_FAIL_DATED = "confirm"

# ACTION_EXPIRED_DATED
# Specifies how incoming messages should be disposed of if they are
# sent to an expired dated address.
# Possible values include:
#
# "bounce"
#    bounce the message - uses BOUNCE_TEXT_EXPIRED_DATED
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
# "hold"
#    silently hold message in pending queue
#
# Default is confirm
if not vars().has_key('ACTION_EXPIRED_DATED'):
    ACTION_EXPIRED_DATED = "confirm"

# ACTION_FAIL_SENDER
# Specifies how incoming messages should be disposed of if they are sent 
# to a sender address, but were not sent from the correct sender, and 
# fail to verify.
# Possible values include:
#
# "bounce"
#    bounce the message - uses BOUNCE_TEXT_FAIL_SENDER
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
# "hold"
#    silently hold message in pending queue
#
# Default is confirm
if not vars().has_key('ACTION_FAIL_SENDER'):
    ACTION_FAIL_SENDER = "confirm"

# ACTION_FAIL_KEYWORD
# Specifies how incoming messages should be disposed of if they are
# sent to a keyword address that fails to verify.
# Possible values include:
#
# "bounce"
#    bounce the message - uses BOUNCE_TEXT_FAIL_KEYWORD
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
# "hold"
#    silently hold message in pending queue
#
# Default is confirm
if not vars().has_key('ACTION_FAIL_KEYWORD'):
    ACTION_FAIL_KEYWORD = "confirm"

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
# The strings which are used to create the HMAC digest are the header
# values only (right hand side of Header:).
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
#
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
# LOGFILE_DEBUG = "/path/to/logs/tmda.debug"
#
# No default.
if not vars().has_key('LOGFILE_DEBUG'):
    LOGFILE_DEBUG = None
    
# LOGFILE_INCOMING
# Filename which incoming delivery (i.e, tmda-filter) summaries should
# be written to.
#
# Example:
# LOGFILE_INCOMING = "/path/to/logs/tmda.in"
#
# No default.
if not vars().has_key('LOGFILE_INCOMING'):
    LOGFILE_INCOMING = None

# LOGFILE_OUTGOING
# Filename which outgoing message (i.e, tmda-sendmail) summaries
# should be written to.
#
# Example:
# LOGFILE_OUTGOING = "/path/to/logs/tmda.out"
#
# No default.
if not vars().has_key('LOGFILE_OUTGOING'):
    LOGFILE_OUTGOING = None

# LOCALDATE
# Set this variable to 0 if you want TMDA to generate ``Date:''
# headers in UTC instead of the local time zone.
#
# Default is 1 (use local time zone)
if not vars().has_key('LOCALDATE'):
    LOCALDATE = 1

# MESSAGE_FROM_STYLE
# Specifies how `From' and `Resent-From' headers should look when
# tagging outgoing messages with tmda-sendmail.  There are two valid
# values:
#
# "address"
#      Just the address - king@grassland.com
#
# "angles"
#      Elvis Parsley <king@grassland.com>
#
# Default is "angles".
if not vars().has_key('MESSAGE_FROM_STYLE'):
    MESSAGE_FROM_STYLE = 'angles'

# MESSAGE_TAG_HEADER_STYLE
# Specifies how headers (other than `From' and `Resent-From') should
# look when tagging outgoing messages with tmda-sendmail.  These are
# the headers such as Reply-To which are defined using the `tag'
# action in your FILTER_OUTGOING file.
#
# The valid values and default value is identical to that of
# MESSAGE_FROM_STYLE.
if not vars().has_key('MESSAGE_TAG_HEADER_STYLE'):
    MESSAGE_TAG_HEADER_STYLE = 'angles'

# MAX_AUTORESPONSES_PER_DAY
# An integer specifying the maximum number of automatic responses sent
# to a given sender address in a day.  This includes _all_
# auto-responses sent by TMDA (confirmation requests, confirmation
# acceptance notices, failure notices, etc.)
#
# This limit prevents response loops between TMDA and misconfigured
# remote auto-responders.  TMDA already inhibits automatic replies to
# any message that looks like a mailing list message or a bounce
# message.  This is a fallback safety valve so it should be set fairly
# high.  Set to 0 for no limit.
#
# Default is 50
if not vars().has_key('MAX_AUTORESPONSES_PER_DAY'):
    MAX_AUTORESPONSES_PER_DAY = 50

# RESPONSE_DIR
# Full path to a directory containing auto-response rate-limiting
# information.  Only consulted if MAX_AUTORESPONSES_PER_DAY != 0
#
# Example:
# RESPONSE_DIR = "/full/path/to/responses/"
#
# Default is ~/.tmda/responses
if not vars().has_key('RESPONSE_DIR') and MAX_AUTORESPONSES_PER_DAY != 0:
    RESPONSE_DIR = os.path.join(DATADIR, 'responses')

# AUTORESPONSE_INCLUDE_SENDER_COPY
# An integer which controls whether a copy of the sender's message is
# included or not when sending an auto response.  Available options:
#
# 0 - do not include any portion of the sender's message.
# 1 - include only the headers from the sender's message.
# 2 - include the sender's entire message.
#
# 2 is *highly* recommended. Not only to give the sender a clear
# indication of which message is being responded to, but also to
# preserve the message for the sender in case she didn't save a copy
# when sending it.
#
# Default is 2
if not vars().has_key('AUTORESPONSE_INCLUDE_SENDER_COPY'):
    AUTORESPONSE_INCLUDE_SENDER_COPY = 2

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

# PENDING_BLACKLIST_APPEND
# Filename to which a sender's e-mail address should be appended
# when a message is "blacklisted" by tmda-pending.
#
# Example:
# PENDING_BLACKLIST_APPEND = "/full/path/to/blacklist"
#
# No default
if not vars().has_key('PENDING_BLACKLIST_APPEND'):
    PENDING_BLACKLIST_APPEND = None

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

# PENDING_WHITELIST_APPEND
# Filename to which a sender's e-mail address should be appended
# when a message is "whitelisted" by tmda-pending.
#
# Example:
# PENDING_WHITELIST_APPEND = "/full/path/to/whitelist"
#
# No default
if not vars().has_key('PENDING_WHITELIST_APPEND'):
    PENDING_WHITELIST_APPEND = None

# ADDED_HEADERS_CLIENT
# A Python dictionary containing one or more header:value string pairs
# that should be added to _all_ outgoing client-side messages (i.e,
# messages sent with tmda-sendmail) prior to injection.  Listed
# headers and their values are case-sensitive.
#
# As the examples below illustrate, the full power of Python is
# available to create these headers -- just make sure both the header
# and its value end up as strings.
#
# Examples:
#
# ADDED_HEADERS_CLIENT = {"X-Fact" : "Father Hennepin Discovered Niagra Falls"}
# import time, os, random
# ADDED_HEADERS_CLIENT = {
#     "X-Localtime" : time.asctime(),
#     "X-Favorite-Author" : "James Joyce",
#     "X-OperatingSystem" : os.uname()[0],
#     "Organization" : os.environ.get("ORGANIZATION"),
#     "X-Uptime" : os.popen("/usr/bin/uptime").read().strip(),
#     "X-Now-Reading" : random.choice(open
#                                     ("/home/jasonrm/.now-reading").
#                                     readlines()).strip()
#     }
#
# No default
if not vars().has_key('ADDED_HEADERS_CLIENT'):
    ADDED_HEADERS_CLIENT = None

# ADDED_HEADERS_SERVER
# A Python dictionary containing one or more header:value string pairs
# that should be added to _all_ outgoing server-side messages (i.e,
# messages sent with tmda-filter) prior to injection.  Listed
# headers and their values are case-sensitive.
#
# See ADDED_HEADERS_CLIENT (above) for some examples.
#
# No default
if not vars().has_key('ADDED_HEADERS_SERVER'):
    ADDED_HEADERS_SERVER = None

# PRIMARY_ADDRESS_MATCH
# An integer which controls how closely the address in the
# ``X-Primary-Address'' header of an incoming messages must match the
# envelope sender address before it's honored.
#
# If the match is close enough, this address will be used for
# CONFIRM_APPEND instead of the envelope sender, and also added to the
# list of addresses checked against FILTER_INCOMING.
#
# This option is available to limit cases of abuse where a sender
# attempts to "whitelist" an address not his own by using an external
# address in an ``X-Primary-Address'' header.
#
# Available options:
#
# 0 - Never a match. Equivalent to disabling X-Primary-Address recognition.
#
# 1 - Identical addresses match. e.g, king@grassland.com and
# king@grassland.com.
#
# 2 - Usernames and hostnames must match. e.g, king@grassland.com and
# king-dated-1037839131.65d080@grassland.com.
#
# 3 - Usernames and domains must match. e.g, king@grassland.com and
# king-dated-1037839131.65d080@memphis.grassland.com.
#
# 4 - Hostnames must match. e.g, king@grassland.com and
# elvis@grassland.com.
#
# 5 - Domains must match. e.g, king@grassland.com and
# elvis@memphis.grassland.com.
#
# 6 - Always a match. e.g, king@grassland.com and elvis@parsely.com.
#
# Default is 5
if not vars().has_key('PRIMARY_ADDRESS_MATCH'):
    PRIMARY_ADDRESS_MATCH = 5

# PURGED_HEADERS
# A list containing one or more message headers that should be removed
# from outgoing client-side messages (i.e, messages sent with
# tmda-sendmail) prior to injection.  Listed headers are
# case-insensitive, and the purging will only be attempted if the
# header actually exists.
#
# NOTE: PURGED_HEADERS is run _after_ ADDED_HEADERS (see above).
#
# Examples:
#
# PURGED_HEADERS = ["bcc", "resent-bcc", "x-mailer"]
# PURGED_HEADERS = ["bcc", "resent-bcc", "x-mailer", "user-agent"]
#
# Default is "Bcc:" and "Resent-Bcc"
if not vars().has_key('PURGED_HEADERS'):
    PURGED_HEADERS = ["bcc", "resent-bcc"]

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

# TAGS_CONFIRM
# A list of one or more strings used to identify a confirmation
# address.  The first element in the list will be used when
# generating a new confirmation address.
#
# Example:
#
# TAGS_CONFIRM = ['confirm', 'c']
#
# Default is 'confirm'
if not vars().has_key('TAGS_CONFIRM'):
    TAGS_CONFIRM = ['confirm']

# TAGS_DATED
# A list of one or more strings used to identify a dated address.  The
# first element in the list will be used by `tmda-address' when
# generating a new dated address.
#
# Example:
#
# TAGS_DATED = ['dated', 'd', 'exp', 'expires']
#
# Default is 'dated'
if not vars().has_key('TAGS_DATED'):
    TAGS_DATED = ['dated']

# TAGS_KEYWORD
# A list of one or more strings used to identify a keyword address.
# The first element in the list will be used by `tmda-address' when
# generating a new keyword address.
#
# Example:
#
# TAGS_KEYWORD = ['keyword', 'key', 'kw']
#
# Default is 'keyword'
if not vars().has_key('TAGS_KEYWORD'):
    TAGS_KEYWORD = ['keyword']

# TAGS_SENDER
# A list of one or more strings to identify a sender address.  The
# first element in the list will be used by `tmda-address' when
# generating a new sender address.
#
# Example:
#
# TAGS_SENDER = ['sender', 's']
#
# Default is 'sender'
if not vars().has_key('TAGS_SENDER'):
    TAGS_SENDER = ['sender']

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

# SUMMARY_HEADERS
# A list containing one or more message headers that should be
# displayed by tmda-pending's interactive mode. Listed headers are
# case-insensitive.
#
# Examples:
#
# SUMMARY_HEADERS = ['from', 'subject', 'x-spam-status']
# SUMMARY_HEADERS = ['date', 'from', 'to', 'subject']
#
# Default is Date, From, To, and Subject.
if not vars().has_key('SUMMARY_HEADERS'):
    SUMMARY_HEADERS = ['date', 'from', 'to', 'subject']

# TIMEOUT
# The timeout interval for 'dated' addresses.  The available units are
# (Y=years, M=months, w=weeks, d=days, h=hours, m=minutes, s=seconds).
#
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

# X_TMDA_IN_SUBJECT
# With this variable set to 1, tmda-inject will parse the Subject
# header looking for `X-TMDA' actions, and then remove them before
# sending the message.  This is useful for users that desire the
# `X-TMDA' override behavior, but don't use an MUA which easily allows
# addition of arbitrary headers (e.g, Outlook).
#
# The Subject header should contain `X-TMDA' followed by whitespace
# followed by the desired action followed by the real subject.  Case
# is insensitive.
#
# Examples:
#
# Subject: X-TMDA dated Re: You're fired!
# Subject:     X-TMDA dated=5M Re: You're fired!
# Subject: X-TMDA   sender      Re: You're fired!
#
# In all cases, the resulting subject will simply be:
# Subject: Re: You're fired!
#
# Default is 0 (turned off)
if not vars().has_key('X_TMDA_IN_SUBJECT'):
    X_TMDA_IN_SUBJECT = 0

###################################
# END of user configurable settings
###################################
