# -*- python -*-

"""Distributed default settings for significant TMDA config variables."""


# Make site-wide configuration changes to this file.  

import os
import stat
import string
import sys

import Util


##############################
# General system-wide defaults
##############################

TMDA_VERSION = "0.30"
TMDA_HOMEPAGE = "<http://tmda.sourceforge.net/>"

PYTHON_VERSION = string.split(sys.version)[0]
# e.g, "TMDA v0.12/Python 2.1 (linux2)"
DELIVERY_AGENT = 'TMDA ' + 'v' + TMDA_VERSION + '/Python ' + PYTHON_VERSION \
                 + ' (' + sys.platform + ')'

# Exit codes: everything except 0, 99 and 100 are soft errors.
ERR_OK = 0          # Success; look at the next .qmail file instruction.
ERR_INTERNAL = 93   # This program has a bug!  How did that happen?
ERR_CONFIG = 94     # Something wrong with the config-file; defer delivery.
ERR_REMOTE = 95     # Remote user error.
ERR_IO = 96         # Problem with, open, read, write, or close; defer delivery.
ERR_STOP = 99       # Success, but don't look further in the .qmail file.
ERR_HARD = 100      # Hard error; bounce message back to sender.
ERR_SOFT = 111      # Soft error; defer delivery.

# Look for the config-file in the environment first then default to ~/.tmdarc.
TMDARC = os.environ.get('TMDARC')
if not TMDARC:TMDARC = os.path.expanduser("~/.tmdarc")

# Read-in the user's configuration file first.
if not os.path.exists(TMDARC):
    print "Can't open configuration file:",TMDARC
    sys.exit(ERR_CONFIG)
execfile(TMDARC)

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
    print TMDARC,"must be permission mode 400 or 600!"
    sys.exit(ERR_CONFIG)
else:
    pass

############################
# User configurable settings
############################

# Only compute defaults for settings not in user's ~/.tmdarc to speed
# startup.
    
# CONFIRMATION_MODE
# Set this variable to 0 if you do not want bounces confirmed for
# validity.
# Default is 1 (turned on)
if not vars().has_key('CONFIRMATION_MODE'):
    CONFIRMATION_MODE = 1

# CONFIRM_ACCEPT_NOTIFY
# Set this variable to 0 if you do not want to generate confirmation
# acceptance notices.
# Default is 1 (turned on)
if not vars().has_key('CONFIRM_ACCEPT_NOTIFY'):
    CONFIRM_ACCEPT_NOTIFY = 1

# BLACKLIST
# Filename which contains a list of e-mail addresses and/or
# substrings, one per line, which are considered unacceptable and
# therefore bounced if there is a match.
# Default is ~/.tmda-blacklist
if not vars().has_key('BLACKLIST'):
    BLACKLIST = os.path.expanduser("~/.tmda-blacklist")

# BOUNCE_BLACKLIST_CC
# An optional e-mail address which will be sent a copy of any message
# that bounces because of a BLACKLIST match.
# No default.
if not vars().has_key('BOUNCE_BLACKLIST_CC'):
    BOUNCE_BLACKLIST_CC = None

# BOUNCE_DATED_CC
# An optional e-mail address which will be sent a copy of any message
# that triggers a 'dated' bounce.
# No default.
if not vars().has_key('BOUNCE_DATED_CC'):
    BOUNCE_DATED_CC = None

# BOUNCE_SENDER_CC
# An optional e-mail address which will be sent a copy of any message
# that triggers a 'sender' bounce.
# No default.
if not vars().has_key('BOUNCE_SENDER_CC'):
    BOUNCE_SENDER_CC = None

# BOUNCE_ENV_SENDER
# The envelope sender of the bounce message. For a normal bounce, this
# should be an empty string.
if not vars().has_key('BOUNCE_ENV_SENDER'):
    BOUNCE_ENV_SENDER = ''

# BOUNCE_DATED_TEMPLATE
# Full path to a custom template for 'dated' bounces.
# Default is bounce_confirm_dated.txt or bounce_dated.txt in
# ../templates/ depending on CONFIRMATION_MODE.
if not vars().has_key('BOUNCE_DATED_TEMPLATE'):
    if CONFIRMATION_MODE:
        d_template = '/templates/bounce_confirm_dated.txt'
    else:
        d_template =  '/templates/bounce_dated.txt'
    BOUNCE_DATED_TEMPLATE = os.path.split(os.path.dirname
                                          (os.path.abspath
                                           (sys.argv[0])))[0] + d_template

# BOUNCE_SENDER_TEMPLATE
# Full path to a custom template for 'sender' bounces.
# Default is bounce_confirm_sender.txt or bounce_sender.txt in
# ../templates/ depending on CONFIRMATION_MODE.
if not vars().has_key('BOUNCE_SENDER_TEMPLATE'):
    if CONFIRMATION_MODE:
        s_template = '/templates/bounce_confirm_sender.txt'
    else:
        s_template = '/templates/bounce_sender.txt'
    BOUNCE_SENDER_TEMPLATE = os.path.split(os.path.dirname
                                           (os.path.abspath
                                            (sys.argv[0])))[0] + s_template 

# CONFIRM_ACCEPT_TEMPLATE
# Full path to a custom template for confirmation acceptance notices.
# Default is confirm_accept.txt in ../templates/.
if not vars().has_key('CONFIRM_ACCEPT_TEMPLATE'):
    ca_template = '/templates/confirm_accept.txt'
    CONFIRM_ACCEPT_TEMPLATE = os.path.split(os.path.dirname
                                            (os.path.abspath
                                             (sys.argv[0])))[0] + ca_template 
    
# COOKIE_TYPE
# The default cookie type is dated.  It could be:
#       dated   can only be replied to for TIMEOUT
#       sender  can only be replied to by address
#       bare    untagged
if not vars().has_key('COOKIE_TYPE'):
    COOKIE_TYPE = "dated"

# CRYPT_KEY
# Your encryption key should be unique and kept secret.
# Use the included "tmda-keygen" program to generate your key.
# No default.
if not vars().has_key('CRYPT_KEY'):
    print "Encryption key not found!"
    sys.exit(ERR_CONFIG)
else:
    # Convert key from hex back into raw binary.
    # Hex has only 4 bits of entropy per byte as opposed to 8.
    CRYPT_KEY = Util.unhexlify(CRYPT_KEY)

# DATADIR
# Top-level directory which TMDA uses to store temporary files and
# directories such as the "pending" queue for yet-to-be-confirmed
# messages.  TMDA should be free to create subdirectories under
# DATADIR if need be.  Make sure to include a traling "/".
# Default is ~/.tmda/
if not vars().has_key('DATADIR'):
    DATADIR = os.path.expanduser("~/.tmda/")

# FULLNAME
# Your full name.
# Default comes from your environment or the password file.
if not vars().has_key('FULLNAME'):
    FULLNAME = Util.getfullname()

# HOSTNAME
# The right-hand side of your email address (after `@').
# Defaults to the fully qualified domain name of the localhost.
if not vars().has_key('HOSTNAME'):
    HOSTNAME = Util.gethostname()

# INJECT
# inject defaults to /var/qmail/bin/qmail-inject, but this lets
# you override it in case it is installed elsewhere.
if not vars().has_key('INJECT'):
     INJECT = "/var/qmail/bin/qmail-inject"
if not os.path.exists(INJECT):
    print "Injection mechanism not found:",INJECT
    sys.exit(ERR_CONFIG)

# INJECT_FLAGS
# inject_flags defaults to `f' (see qmail-inject(8) for flag descriptions)
if not vars().has_key('INJECT_FLAGS'):
    INJECT_FLAGS = "f"

# LOCALS
# locals defaults to /var/qmail/crontrol/locals, but this lets you
# override it in case it is installed elsewhere.
# Used for virtualdomain detection in tmda-filter.
if not vars().has_key('LOCALS'):
     LOCALS = "/var/qmail/control/locals"
if not os.path.exists(LOCALS):
    print "file not found:",LOCALS
    sys.exit(ERR_CONFIG)

# LOGFILE
# Filename which delivery statistics should be written to.
# Default is 0 (no logging)
if not vars().has_key('LOGFILE'):
    LOGFILE = 0

# TIMEOUT
# The timeout interval for 'dated' addresses.  The units can be
# (w=weeks, d=days, h=hours, m=minutes, s=seconds).
# Default is 5d (5 days).
if not vars().has_key('TIMEOUT'):
    TIMEOUT = "5d"

# USERNAME
# The left-hand side of your e-mail address (before `@').
# Defaults to your UNIX username.
if not vars().has_key('USERNAME'):
    USERNAME = Util.getusername()

# USERPREFIX
# The prefix to the address as specified in the last field of the
# /var/qmail/users/assign. (without a trailing `-')
# No default.
if not vars().has_key('USERPREFIX'):
    USERPREFIX = None
    
# BARE_FILE
# Filename which contains a list of e-mail addresses, one per line,
# which will receive untagged (no cookie added) messages.
# Default is ~/.tmda-bare
if not vars().has_key('BARE_FILE'):
    BARE_FILE = os.path.expanduser("~/.tmda-bare")

# DATED_FILE
# Filename which contains a list of e-mail addresses, one per line,
# which will receive messages with a dated cookie added to your
# address.
# Default is ~/.tmda-dated
if not vars().has_key('DATED_FILE'):
    DATED_FILE = os.path.expanduser("~/.tmda-dated")

# EXP_FILE
# Filename which contains a list of explicit to/from pairs, one per
# line.  If mail is destined for `to', your address will be changed
# to `from'.  For example,
#
#  xemacs-announce@xemacs.org jason@xemacs.org
#  domreg@internic.net        hostmaster@mastaler.com
#
# Default is ~/.tmda-exp
if not vars().has_key('EXP_FILE'):
    EXP_FILE = os.path.expanduser("~/.tmda-exp")

# EXT_FILE
# Filename which contains a list of e-mail address/extension pairs,
# one per line, which will receive messages with the extension added
# to the username of your address.  For example,
#
#  xemacs-beta@xemacs.org list-xemacs-beta
#  qmail@list.cr.yp.to    list-qmail
#
# Default is ~/.tmda-ext
if not vars().has_key('EXT_FILE'):
    EXT_FILE = os.path.expanduser("~/.tmda-ext")

# SENDER_FILE
# Filename which contains a list of e-mail addresses, one per line,
# which will receive messages with a sender cookie added to your
# address.
# Default is ~/.tmda-sender
if not vars().has_key('SENDER_FILE'):
    SENDER_FILE = os.path.expanduser("~/.tmda-sender")

# WHITELIST
# Filename which contains a list of e-mail addresses and/or
# substrings, one per line, which are considered trusted contacts and
# therefore allowed directly into your mailbox if there is a match.
# Default is ~/.tmda-whitelist
if not vars().has_key('WHITELIST'):
    WHITELIST = os.path.expanduser("~/.tmda-whitelist")

# WHITELIST_TO_BARE
# Set this variable to 1 if you want addresses in your
# WHITELIST to receive untagged (no cookie added) messages.
# Default is 0 (turned off)
if not vars().has_key('WHITELIST_TO_BARE'):
    WHITELIST_TO_BARE = 0

###################################
# END of user configurable settings
###################################
