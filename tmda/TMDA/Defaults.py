# -*- python -*-

"""TMDA configuration variable defaults."""


import os
import stat
import string
import sys

import Util


##############################
# General system-wide defaults
##############################

TMDA_VERSION = "0.38"
TMDA_HOMEPAGE = "<http://tmda.sf.net/>"

PYTHON_VERSION = string.split(sys.version)[0]
# e.g, "TMDA v0.35/Python 2.1.1 (irix646)"
DELIVERY_AGENT = 'TMDA ' + 'v' + TMDA_VERSION + '/Python ' + PYTHON_VERSION \
                 + ' (' + sys.platform + ')'

# qmail exit codes: everything except 0, 99 and 100 are soft errors.
ERR_OK = 0          # Success; look at the next .qmail file instruction.
ERR_INTERNAL = 93   # This program has a bug!  How did that happen?
ERR_CONFIG = 94     # Something wrong with the config-file; defer delivery.
ERR_REMOTE = 95     # Remote user error.
ERR_IO = 96         # Problem with open, read, write, or close; defer delivery.
ERR_STOP = 99       # Success, but don't look further in the .qmail file.
ERR_HARD = 100      # Hard error; bounce message back to sender.
ERR_SOFT = 111      # Soft error; defer delivery.

# If the file /etc/tmdarc exists, read it before ~/.tmdarc.
# Make site-wide configuration changes to this file.
GLOBAL_TMDARC = '/etc/tmdarc'
if os.path.exists(GLOBAL_TMDARC):
    try:
        execfile(GLOBAL_TMDARC)
    except IOError:
        pass                            # just skip it if we can't open it
    
# Look for the user-config-file in the environment first then default
# to ~/.tmdarc.
TMDARC = os.environ.get('TMDARC')
if not TMDARC:TMDARC = os.path.expanduser("~/.tmdarc")

# Read-in the user's configuration file.
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

# Only compute defaults for unset variables to speed startup.

# DATADIR
# Top-level directory which TMDA uses to store its files and
# directories.  TMDA should be free to create files and directories
# under DATADIR if need be.  Make sure to include a trailing "/".
# Default is ~/.tmda/
if not vars().has_key('DATADIR'):
    DATADIR = os.path.expanduser("~/.tmda/")

# SENDMAIL
# The path to the sendmail program, or sendmail compatibility
# interface.  Defaults to one of the two standard locations, but you
# can override it in case it is installed elsewhere.
if not vars().has_key('SENDMAIL'):
    if os.path.exists("/usr/sbin/sendmail"):
        SENDMAIL = "/usr/sbin/sendmail"
    elif os.path.exists("/usr/lib/sendmail"):
        SENDMAIL = "/usr/lib/sendmail"
    else:
        print "Can't find your sendmail program!"
        sys.exit(ERR_CONFIG)
else:
    if not os.path.exists(SENDMAIL):
        print "invalid sendmail program path:",SENDMAIL
        sys.exit(ERR_CONFIG)

# RECIPIENT_DELIMITER
# A single character which specifies the separator between user names
# and address extensions (e.g, user-ext).
# The default under qmail is `-', while the default for Sendmail and
# friends is likely `+'.  Postfix has a config variable named
# `recipient_delimiter' that defines this character.
if not vars().has_key('RECIPIENT_DELIMITER'):
    RECIPIENT_DELIMITER = "-"

# USEVIRTUALDOMAINS
# Set this variable to 0 if want to turn off TMDA's virtualdomains
# support.  This should obviously only be done if you are not running
# any virtualdomains, but it will improve performance.
# Default is 1 (turned on)
if not vars().has_key('USEVIRTUALDOMAINS'):
    USEVIRTUALDOMAINS = 1

# VIRTUALDOMAINS
# virtualdomains defaults to /var/qmail/control/virtualdomains, but
# this lets you override it in case it is installed elsewhere.  Used
# for virtualdomain processing in tmda-filter.
if not vars().has_key('VIRTUALDOMAINS'):
    VIRTUALDOMAINS = "/var/qmail/control/virtualdomains"

# BLACKLIST
# Filename which contains a list of e-mail addresses and/or
# substrings, one per line, which are considered unacceptable and
# therefore bounced if there is a match.
# Default is ~/.tmda/lists/blacklist
if not vars().has_key('BLACKLIST'):
    BLACKLIST = DATADIR + "lists/" + "blacklist"

# BOUNCE_BLACKLIST_CC
# An optional e-mail address which will be sent a copy of any message
# that bounces because of a BLACKLIST match.
# No default.
if not vars().has_key('BOUNCE_BLACKLIST_CC'):
    BOUNCE_BLACKLIST_CC = None

# BOUNCE_CONFIRM_CC
# An optional e-mail address which will be sent a copy of any message
# that triggers a confirmation request.
# No default.
if not vars().has_key('BOUNCE_CONFIRM_CC'):
    BOUNCE_CONFIRM_CC = None

# BOUNCE_REVOKED_CC
# An optional e-mail address which will be sent a copy of any message
# that bounces because of a REVOKED match.
# No default.
if not vars().has_key('BOUNCE_REVOKED_CC'):
    BOUNCE_REVOKED_CC = None

# BOUNCE_ENV_SENDER
# The envelope sender of the bounce message. For a normal bounce, this
# should be an empty string.
if not vars().has_key('BOUNCE_ENV_SENDER'):
    BOUNCE_ENV_SENDER = ''

# CONFIRM_ACCEPT_NOTIFY
# Set this variable to 0 if you do not want to generate confirmation
# acceptance notices.
# Default is 1 (turned on)
if not vars().has_key('CONFIRM_ACCEPT_NOTIFY'):
    CONFIRM_ACCEPT_NOTIFY = 1

# CONFIRM_MAX_MESSAGE_SIZE
# This is the largest size (in bytes) that a message can be before the
# its body is excluded from the confirmation request/acceptance
# notice.  Set this to None to allow any size message.
# Default is 50000
if not vars().has_key('CONFIRM_MAX_MESSAGE_SIZE'):
    CONFIRM_MAX_MESSAGE_SIZE = 50000

# CONFIRM_ACCEPT_TEMPLATE
# Full path to a custom template for confirmation acceptance notices.
# Default is confirm_accept.txt in ../templates/.
if not vars().has_key('CONFIRM_ACCEPT_TEMPLATE'):
    ca_template = '/templates/confirm_accept.txt'
    CONFIRM_ACCEPT_TEMPLATE = os.path.split(os.path.dirname
                                            (os.path.abspath
                                             (sys.argv[0])))[0] + ca_template 

# CONFIRM_REQUEST_TEMPLATE
# Full path to a custom template for confirmation requests.
# Default is confirm_request.txt in ../templates/.
if not vars().has_key('CONFIRM_REQUEST_TEMPLATE'):
    cr_template = '/templates/confirm_request.txt'
    CONFIRM_REQUEST_TEMPLATE = os.path.split(os.path.dirname
                                            (os.path.abspath
                                             (sys.argv[0])))[0] + cr_template 

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

# COOKIE_TYPE
# The default cookie type is dated.  Possible values are:
#       dated   (can only be replied to for TIMEOUT)
#       sender  (can only be replied to by address)
#       bare    (untagged)
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

# FULLNAME
# Your full name.
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

# LOGFILE
# Filename which delivery statistics should be written to.
# Default is 0 (no logging)
if not vars().has_key('LOGFILE'):
    LOGFILE = 0

# TIMEOUT
# The timeout interval for 'dated' addresses.  The available units are
# (Y=years, M=months, w=weeks, d=days, h=hours, m=minutes, s=seconds).
# Default is 5d (5 days).
if not vars().has_key('TIMEOUT'):
    TIMEOUT = "5d"

# USERNAME
# The left-hand side of your e-mail address (before `@').
# Defaults to your UNIX username.
if not vars().has_key('USERNAME'):
    USERNAME = Util.getusername()

# BARE_FILE
# Filename which contains a list of e-mail addresses, one per line,
# which will receive untagged (no cookie added) messages.
# Default is ~/.tmda/lists/bare
if not vars().has_key('BARE_FILE'):
    BARE_FILE = DATADIR + "lists/" + "bare"

# DATED_FILE
# Filename which contains a list of e-mail addresses, one per line,
# which will receive messages with a dated cookie added to your
# address.
# Default is ~/.tmda/lists/dated
if not vars().has_key('DATED_FILE'):
    DATED_FILE = DATADIR + "lists/" + "dated"

# EXP_FILE
# Filename which contains a list of explicit to/from pairs, one per
# line.  If mail is destined for `to', your address will be changed
# to `from'.  For example,
#
#  xemacs-announce@xemacs.org jason@xemacs.org
#  domreg@internic.net        hostmaster@mastaler.com
#
# Default is ~/.tmda/lists/exp
if not vars().has_key('EXP_FILE'):
    EXP_FILE = DATADIR + "lists/" + "exp"

# EXT_FILE
# Filename which contains a list of e-mail address/extension pairs,
# one per line, which will receive messages with the extension added
# to the username of your address.  For example,
#
#  xemacs-beta@xemacs.org list-xemacs-beta
#  qmail@list.cr.yp.to    list-qmail
#
# Default is ~/.tmda/lists/ext
if not vars().has_key('EXT_FILE'):
    EXT_FILE = DATADIR + "lists/" + "ext"

# REVOKED_FILE
# Filename which contains a list of recipient e-mail addresses, one
# per line, which have been "revoked" and will therefore bounce.
# Default is ~/.tmda/lists/revoked
if not vars().has_key('REVOKED_FILE'):
    REVOKED_FILE = DATADIR + "lists/" + "revoked"
    
# SACRED_FILE
# Filename which contains a list of sacred keywords, the presence
# of which automatically zaps the mail into your mailbox.
# Default is ~/.tmda/lists/sacred
if not vars().has_key('SACRED_FILE'):
    SACRED_FILE = DATADIR + "lists/" + "sacred"

# SENDER_FILE
# Filename which contains a list of e-mail addresses, one per line,
# which will receive messages with a sender cookie added to your
# address.
# Default is ~/.tmda/lists/sender
if not vars().has_key('SENDER_FILE'):
    SENDER_FILE = DATADIR + "lists/" + "sender"

# WHITELIST
# Filename which contains a list of e-mail addresses and/or
# substrings, one per line, which are considered trusted contacts and
# therefore allowed directly into your mailbox if there is a match.
# Default is ~/.tmda/lists/whitelist
if not vars().has_key('WHITELIST'):
    WHITELIST = DATADIR + "lists/" + "whitelist"

# WHITELIST_AUTO_APPEND
# If you set this variable to 1, once a sender confirms a message their
# e-mail address will be automatically appended to WHITELIST.
# Default is 0 (turned off)
if not vars().has_key('WHITELIST_AUTO_APPEND'):
    WHITELIST_AUTO_APPEND = 0

# WHITELIST_TO_BARE
# Set this variable to 0 if you don't want addresses in your WHITELIST
# to automatically receive untagged (no cookie added) messages.
# Default is 1 (turned on)
if not vars().has_key('WHITELIST_TO_BARE'):
    WHITELIST_TO_BARE = 1

###################################
# END of user configurable settings
###################################
