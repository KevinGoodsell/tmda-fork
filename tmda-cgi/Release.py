#!/usr/bin/env python
#
# Copyright (C) 2002 Gre7g Luterman <gre7g@wolfhome.com>
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

"""Web release for tmda-cgi.

This module is run when a user clicks a URL in a confirmation e-mail."""

import cgi
import os
import pwd
import re
import CgiUtil
import MyCgiTb
import Template
from email.Utils import parseaddr
from TMDA import Util
from TMDA import Errors

def Release(QueryString):
  """Release the message represented in the QueryString.

QueryString is in the format <UID>.<timestamp>.<PID>.<HMAC>

Where <UID> is the UID of the TMDA account, <HMAC> must be used to validate
<timestamp>.<PID>, and the pending e-mail filename is  "<timestamp>.<PID>.msg".
"""

  # Prepare the traceback in case of uncaught exception
  MyCgiTb.Content()
  MyCgiTb.ErrTemplate = "prog_err2.html"
  CgiUtil.ErrTemplate = "error2.html"

  try:
    UID, Timestamp, PID, HMAC = QueryString.split(".")
    UID = int(UID)
    UserRec = pwd.getpwuid(UID)
    User = UserRec[0]
    GID = UserRec[3]
  except ValueError:
    CgiUtil.TermError("Unable to parse query string." % \
      (Timestamp, PID, HMAC), "Program error / corrupted link.",
      "locate pending e-mail", "",
      "Recheck link or contact TMDA programmers.")
  MsgID = "%s.%s.msg" % (Timestamp, PID)

  # Check to make sure they're not trying to access anything other than email
  if not re.compile("^\d+\.\d+\.msg$").search(MsgID):
    CgiUtil.TermError("<tt>%s.%s.%s</tt> is not a valid message ID." % \
      (Timestamp, PID, HMAC), "Program error / corrupted link.",
      "retrieve pending e-mail", "",
      "Recheck link or contact TMDA programmers.")

  os.environ["USER"] = User
  os.environ["HOME"] = Util.gethomedir(User)

  # Is there a TMDARC variable?
  if os.environ.has_key("TMDARC"):
    # Yes, replace it
    os.environ["TMDARC"] = os.environ["TMDARC"].replace("/~/", "/%s/" % User)

  # Try to change users
  try:
    os.seteuid(0)
    os.setegid(0)
    os.setegid(GID)
    os.seteuid(UID)
  except OSError:
    pass

  # Now that we know who we are, get our defaults
  from TMDA import Defaults
  from TMDA import Pending
  from TMDA import Cookie

  try:
    Defaults.CRYPT_KEY
  except AttributeError:
    CgiUtil.TermError("Could not read CRYPT_KEY.",
      "CRYPT_KEY can not be read by group %d." % os.getegid(),
      "read CRYPT_KEY", "ALLOW_MODE_640 = %d<br>%s" % (Defaults.ALLOW_MODE_640,
      CgiUtil.FileDetails("Cryptography key", Defaults.CRYPT_KEY_FILE)),
      """Any of the following solutions:<br>
1. Place <tt>%s</tt> in any of the groups that user %d belongs to.<br>
2. Do all three of the following:<br>
&nbsp;&nbsp;&nbsp;&#8226; Place <tt>%s</tt> in group %d.<br>
&nbsp;&nbsp;&nbsp;&#8226; Assign permissions 640 to <tt>%s</tt>.<br>
&nbsp;&nbsp;&nbsp;&#8226; Set ALLOW_MODE_640 = 1 in your configuration file.<br>
3. Disable URL confirmation in your confirmation template.""" %
(Defaults.CRYPT_KEY_FILE, os.geteuid(), Defaults.CRYPT_KEY_FILE, os.getegid(),
Defaults.CRYPT_KEY_FILE))

  # Validate the HMAC
  if Cookie.confirmationmac(Timestamp, PID, "accept") != HMAC:
    CgiUtil.TermError("<tt>%s.%s.%s</tt> is not a valid message ID." % \
      (Timestamp, PID, HMAC), "Program error / corrupted link.",
      "retrieve pending e-mail", "",
      "Recheck link or contact TMDA programmers.")

  # Read in e-mail
  try:
    MsgObj = Pending.Message(MsgID)
  except Errors.MessageError:
    CgiUtil.TermError("Message could not be fetched.",
      "Message has already been released or deleted.",
      "retrieve pending e-mail", "",
      "Inquire with recipient about e-mail.")

  T = Template.Template("released.html")

  # Fetch row
  Row = T["Row"]

  # Generate header rows
  for Header in Defaults.SUMMARY_HEADERS:
    T["Name"]  = Header.capitalize()
    T["Value"] = CgiUtil.Escape(MsgObj.msgobj[Header])
    Row.Add()

  # Can we add this address to a do-not-confirm-again list?
  if Defaults.CONFIRM_APPEND:
    ConfirmAddr = Util.confirm_append_address \
    (
      parseaddr(MsgObj.msgobj["x-primary-address"])[1],
      parseaddr(MsgObj.msgobj["return-path"])[1]
    )
    if ConfirmAddr:
      Util.append_to_file(ConfirmAddr, Defaults.CONFIRM_APPEND)
      T["Address"] = ConfirmAddr
    else:
      T["Future"]
  else:
    T["Future"]

  print T

  # Make sure release does not write to PENDING_RELEASE_APPEND
  Defaults.PENDING_RELEASE_APPEND = None

  MsgObj.release()
