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

TMDA_VERSION = "0.43"
TMDA_HOMEPAGE = "<http://tmda.sf.net/>"

PYTHON_VERSION = string.split(sys.version)[0]
# e.g, "TMDA v0.35/Python 2.1.1 (irix646)"
DELIVERY_AGENT = 'TMDA ' + 'v' + TMDA_VERSION + '/Python ' + PYTHON_VERSION \
                 + ' (' + sys.platform + ')'

# The current process id of the Python interpreter as a string.
PID = str(os.getpid())

# General exit status codes which should be understood by all MTAs.
# Defined so we can raise exit codes within TMDA modules without
# having to create an MTA instance.
EX_OK = 0                               
EX_TEMPFAIL = 75

# If the file /etc/tmdarc exists, read it before ~/.tmdarc.
# Make site-wide configuration changes to this file.
GLOBAL_TMDARC = '/etc/tmdarc'
if os.path.exists(GLOBAL_TMDARC):
    try:
        execfile(GLOBAL_TMDARC)
    except:
        pass                            # just skip it if there is a problem
        
# Look for the user-config-file in the environment first then default
# to ~/.tmdarc.
TMDARC = os.environ.get('TMDARC')
if not TMDARC:TMDARC = os.path.expanduser("~/.tmdarc")

# Read-in the user's configuration file.
if not os.path.exists(TMDARC):
    print "Can't open configuration file:",TMDARC
    sys.exit(EX_TEMPFAIL)
else:
    try:
        execfile(TMDARC)
    except Exception, error_msg:
        print TMDARC, error_msg
        sys.exit(EX_TEMPFAIL)
                
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
    sys.exit(EX_TEMPFAIL)
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

# MAIL_TRANSFER_AGENT
# Defines which mail transfer agent (MTA) software you are running.
# Possible choices are "exim", "postfix" or "qmail"
# Default is qmail
if not vars().has_key('MAIL_TRANSFER_AGENT'):
    MAIL_TRANSFER_AGENT = "qmail"

# LOCAL_DELIVERY_AGENT
# The full path to the program used to deliver a sucessful message to
# your mailbox.  Only necessary if you are NOT running qmail!
# Tested LDAs include maildrop and procmail.
# This variable may also contain arguments which will be passed to the command.
# e.g, LOCAL_DELIVERY_AGENT = "/usr/bin/procmail -p ~/.procmailrc"
# No default
if not vars().has_key('LOCAL_DELIVERY_AGENT'):
    LOCAL_DELIVERY_AGENT = None
if MAIL_TRANSFER_AGENT != 'qmail' and not LOCAL_DELIVERY_AGENT:
    print "Not running qmail: you must define LOCAL_DELIVERY_AGENT in",TMDARC
    sys.exit(EX_TEMPFAIL)

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
    if os.path.exists("/usr/sbin/sendmail"):
        SENDMAIL = "/usr/sbin/sendmail"
    elif os.path.exists("/usr/lib/sendmail"):
        SENDMAIL = "/usr/lib/sendmail"
    else:
        print "Can't find your sendmail program!"
        sys.exit(EX_TEMPFAIL)
elif not os.path.exists(SENDMAIL):
    print "Invalid SENDMAIL path:",SENDMAIL
    sys.exit(EX_TEMPFAIL)

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
# Default is an empty envelope sender <>.
if not vars().has_key('BOUNCE_ENV_SENDER'):
    # Exim doesn't like -f ''
    if MAIL_TRANSFER_AGENT == 'exim':
        BOUNCE_ENV_SENDER = '<>'
    else:
        BOUNCE_ENV_SENDER = ''

# BARE_APPEND
# Filename to which a recipient's e-mail address should be
# automatically appended if the outgoing <action> is in the form
# 'bare=append'.
# No default
if not vars().has_key('BARE_APPEND'):
    BARE_APPEND = None

# CONFIRM_APPEND
# Filename to which a sender's e-mail address should be automatically
# appended once they confirm a message.  This can be used to implement
# "auto-whitelisting" functionality.
# No default
if not vars().has_key('CONFIRM_APPEND'):
    CONFIRM_APPEND = None

# CONFIRM_CC
# An optional e-mail address which will be sent a copy of any message
# that triggers a confirmation request.
# No default.
if not vars().has_key('CONFIRM_CC'):
    CONFIRM_CC = None

# CONFIRM_ACCEPT_NOTIFY
# Set this variable to 0 if you do not want to generate confirmation
# acceptance notices.
# Default is 1 (turned on)
if not vars().has_key('CONFIRM_ACCEPT_NOTIFY'):
    CONFIRM_ACCEPT_NOTIFY = 1

# CONFIRM_ACCEPT_CC
# An optional e-mail address which will be sent a copy of the
# confirmation acceptance messages people send you.
if not vars().has_key('CONFIRM_ACCEPT_CC'):
    CONFIRM_ACCEPT_CC = None

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

# CRYPT_KEY
# Your encryption key should be unique and kept secret.
# Use the included "tmda-keygen" program to generate your key.
# No default.
if not vars().has_key('CRYPT_KEY'):
    print "Encryption key not found!"
    sys.exit(EX_TEMPFAIL)
else:
    # Convert key from hex back into raw binary.
    # Hex has only 4 bits of entropy per byte as opposed to 8.
    CRYPT_KEY = Util.unhexlify(CRYPT_KEY)

# FILTER_INCOMING
# Filter file which controls how incoming messages are tagged.
# Default is ~/.tmda/filters/incoming
# Look for the filter-file in the environment first.
env_FILTER_INCOMING = os.environ.get('TMDA_FILTER_INCOMING')
if env_FILTER_INCOMING:
    FILTER_INCOMING = env_FILTER_INCOMING
elif not vars().has_key('FILTER_INCOMING'):
    FILTER_INCOMING = DATADIR + "filters/" + "incoming"

# FILTER_OUTGOING
# Filter file which controls how outgoing messages are tagged.
# Default is ~/.tmda/filters/outgoing
# Look for the filter-file in the environment first.
env_FILTER_OUTGOING = os.environ.get('TMDA_FILTER_OUTGOING')
if env_FILTER_OUTGOING:
    FILTER_OUTGOING = env_FILTER_OUTGOING
elif not vars().has_key('FILTER_OUTGOING'):
    FILTER_OUTGOING = DATADIR + "filters/" + "outgoing"
    
# FILTER_BOUNCE_CC
# An optional e-mail address which will be sent a copy of any message
# that bounces because of a match in FILTER_INCOMING.
# No default.
if not vars().has_key('FILTER_BOUNCE_CC'):
    FILTER_BOUNCE_CC = None

# FILTER_DROP_CC
# An optional e-mail address which will be sent a copy of any message
# that is dropped because of a match in FILTER_INCOMING.
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
# "bare"
#    don't tag
#
# "dated"
#    tag with a dated address
#
# "sender"
#    tag with a sender address
#
# Default is dated
if not vars().has_key('ACTION_OUTGOING'):
    ACTION_OUTGOING = "dated"

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

# LOGFILE
# Filename which delivery statistics should be written to.
# Default is 0 (no logging)
if not vars().has_key('LOGFILE'):
    LOGFILE = 0

# MESSAGE_FROM_STYLE
# Specifies how `From' headers should look on when tagging outgoing
# messages with tmda-inject.  There are three valid values:
#
#     "address"
#           Just the address - king@grassland.com
#
#     "parens"
#           king@grassland.com (Elvis Parsley)
#
#     "angles"
#           "Elvis Parsley" <king@grassland.com>
#
#     "unquoted"
#           Elvis Parsley <king@grassland.com>
#           (only use if you know your fullname doesn't need
#           double-quotes; see rfc2822 for clarification)
#
# Default is "angles".
if not vars().has_key('MESSAGE_FROM_STYLE'):
    MESSAGE_FROM_STYLE = "angles"

# TIMEOUT
# The timeout interval for 'dated' addresses.  The available units are
# (Y=years, M=months, w=weeks, d=days, h=hours, m=minutes, s=seconds).
# Default is 5d (5 days).
if not vars().has_key('TIMEOUT'):
    TIMEOUT = "5d"

# TIMEZONE
# A string representing a valid timezone on your system.  e.g,
#
# TIMEZONE = "MST7MDT"
# TIMEZONE = "Pacific/Auckland"
#
# If you define this variable, the `TZ' environment variable will be
# set to its result.  This might be useful when you want dates
# represented (in logfiles, mail headers, etc.) in a timezone other
# than the default timezone of the machine running TMDA.
# Default is the timezone of the local host.
if not vars().has_key('TIMEZONE'):
    TIMEZONE = None
# The time module gets the timezone name when first imported, and it
# can't be changed by later setting TZ in the environment.  Thus, we
# must set TZ first, or else the time-zone as hour offset from UTC
# will be incorrect.
else:
    os.environ['TZ'] = TIMEZONE

# USERNAME
# The left-hand side of your e-mail address (before `@').
# Defaults to your UNIX username.
if not vars().has_key('USERNAME'):
    USERNAME = Util.getusername()

###################################
# END of user configurable settings
###################################
