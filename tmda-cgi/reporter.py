#!/usr/bin/env python -O

"""SpamCop Reporting Program. 

Copyright (c) 2001,2002, Alan Eldridge.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

History:

Started as a Python version (by Oleg BroytMann) of a Perl program
found at http://spamcop.net/fom-serve/cache/166.html. However, no
part of Oleg's code remains, and this version is released under the
BSD license with my copyright.

"""
#
# This program accepts SPAM on standard input and sends it to SpamCop.
#
# $Id$
#
# Change Log
# ========================================
# 2001/05/28
#   Read from /dev/tty removed; set subject to timestamp + from_addr.
# 2001/11/10
#   Updated for new spamcop user-specific addresses; Use MAILNAME to
#   set from address, if set.
# 2002/01/02
#   filter text added by Mail::Spam-Assassin.
# 2002/03/02
#   Default to stdout if no email addrs found; let sendmail figure out
#   the 'from' address;  make a SpamcopConf object to hold config info.
# 2002/03/07
#   Filter (XXXX) username and domain name, so
#   spammer can't extract it; updated to SpamCop
#   forum.
# 2002/03/07
#   Use textsub regex matching to deal with problems about overlapping
#   strings to hide.
# 2003/11/12 - Tim Legant
#   Ripped out all address/domain hiding code.  SpamCop is now complaining
#   about that.
# 

import getopt
import os
import re
import sys
import time


class SpamcopConf:
    def __init__(self):
        pid = os.getpid()
        tm = time.localtime(time.time())
        self.mailto = None
        self.sendmail = "/usr/sbin/sendmail"
        self.MIME_delim = 'DeathToSpammers' * 3 + '%05d' % (pid,)
        self.subject = time.strftime("SPAM REPORT %Y/%m/%d %H:%M:%S %Z", tm)
    def set_mailto(self, val):
        self.mailto = val
    def set_sendmail(self, val):
        self.sendmail = val

def usage(ec):
    print """
usage: spamcop [Options] [spamcop-email-address]

Options:
    -h			show this help and exit
    -V			show version and exit
    -s sendmail-path	set path to sendmail program
Notes:

1. Spamcop now uses per-user spam submission email addresses.  You
   should supply a spamcop address that you got when you registered with
   spamcop. If you don't have your own spamcop email submission address,
   please register for one now at http://spamcop.net/anonsignup.shtml.
2. The environment var SPAMCOP_MAIL is used if no destination address
   is given on the command line.
3. If no address is given on the command line, and the environment var
   SPAMCOP_MAIL is not set, the message is written to standard output.
4. The environment var SPAMCOP_SENDMAIL is equivalent to '-s' option.
"""
    sys.exit(ec)
   
def sendspam(spam, seq, conf):
    if conf.mailto:
        mailto = conf.mailto
        outfile = os.popen("%s -oi -t" % (conf.sendmail,), 'w')
    else:
        mailto = 'SPAMCOP'
        outfile = sys.stdout
    subjstr = "%s #%03d" % (conf.subject, seq)
    # headers
    outfile.write("""To: %s
Subject: %s
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="%s"

This is a multi-part message in MIME format.

--%s
Content-Type: message/rfc822
Content-Disposition: attachment

""" % (mailto, subjstr, conf.MIME_delim, conf.MIME_delim))
    # copy message
    skip = 0
    body = 0
    for l in spam:
        if re.match(r"^Subject:\s+\*+SPAM\*+\s+", l):
            outfile.write(re.sub(r"\s+\*+SPAM\*+", "", l, 1))
        elif re.match(r"^X-Spam-", l):
            skip = 1
        elif re.match(r"^SPAM:\s+", l):
            skip = 2
        elif skip and re.match(r"^\s+\S", l):
            pass
        elif skip > 1 and re.match(r"^\s*$", l):
            skip = 0
            body = 1
        else:
            skip = 0
            outfile.write(l)
    # finish MIME part
    outfile.write("\n\n--%s\n\n" % (conf.MIME_delim,))
    # report success
    sys.stderr.write("Message '%s' sent to %s\n"
                     % (subjstr, mailto))

def write_mail(spam, conf):
    spams = []
    currspam = []
    for l in spam:
        if l[0:5] == "From ":
            if len(currspam):
                spams.append(currspam)
            currspam = []
        currspam.append(l)
    if len(currspam):
        spams.append(currspam)
    cnt = 0
    for currspam in spams:
        cnt = cnt + 1
        sendspam(currspam, cnt, conf)

# main()

Gconf = SpamcopConf()

if os.environ.has_key('SPAMCOP_MAIL'):
    Gconf.set_mailto(os.environ['SPAMCOP_MAIL'])
if os.environ.has_key('SPAMCOP_SENDMAIL'):
    Gconf.set_sendmail(os.environ['SPAMCOP_SENDMAIL'])

opts, args = getopt.getopt(sys.argv[1:], "hVs:")

for (opt,val) in opts:
    if opt == '-h':
        usage(0)
    elif opt == '-V':
        print '%s: $Revision$' % (sys.argv[0],)
        sys.exit(0)
    elif opt == '-s':
        Gconf.set_sendmail(val)

if len(args) > 0:
    Gconf.set_mailto(' '.join(args))

write_mail(sys.stdin.readlines(), Gconf)

#
#EOF

