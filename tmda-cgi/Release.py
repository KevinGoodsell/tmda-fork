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

QueryString is in one of two formats, real users MAY confirm with:

<UID>.<confirm_cookie>

Virtual users MUST confirm with:

<UID>&<recipient_address>&<confirm_cookie>

Where <UID> is the UID of the TMDA account, <recipient_address> is the untagged
address of the original message recipient, and <confirm_cookie> is used to find
and validate the pending email in question."""

  # Prepare the traceback in case of uncaught exception
  MyCgiTb.ErrTemplate = "prog_err2.html"
  CgiUtil.ErrTemplate = "error2.html"

  try:
    UID, Recipient, Cookie = QueryString.split("&")
    UID = int(UID)
    OldStyle = 0

    # Get base address from Recipient
    RecipUser, RecipDomain = Recipient.split("@")
    User = RecipUser.split('-')[0] + "@" + RecipDomain
  except (ValueError, KeyError):
    try:
      # Check for old-style format
      UID, Cookie = QueryString.split(".", 1)
      UID = int(UID)
      User = pwd.getpwuid(UID)[0]
      OldStyle = 1
    except (ValueError, KeyError):
      CgiUtil.TermError("Unable to parse query string.",
        "Program error / corrupted link.",
        "locate pending e-mail", "", """Please check the link you followed and
make sure that it is typed in exactly as it was sent to you.""")
  try:
    # Get real user from UID
    Timestamp, PID, HMAC = Cookie.split(".")
  except ValueError:
    CgiUtil.TermError("Unable to parse query string.",
      "Program error / corrupted link.",
      "locate pending e-mail", "", """Please check the link you followed and
make sure that it is typed in exactly as it was sent to you.""")

  MsgID = "%s.%s.msg" % (Timestamp, PID)
  # Check to make sure they're not trying to access anything other than email
  if not re.compile("^\d+\.\d+\.msg$").search(MsgID):
    CgiUtil.TermError("<tt>%s.%s.%s</tt> is not a valid message ID." % \
      (Timestamp, PID, HMAC), "Program error / corrupted link.",
      "retrieve pending e-mail", "", """Please check the link you followed and
make sure that it is typed in exactly as it was sent to you.""")

  # Set up the user's home directory.
  try:
    os.seteuid(0)
    os.setegid(0)
    os.setuid(0)
  except OSError:
    pass
  try:
    if os.environ.has_key("TMDA_VLOOKUP") and not OldStyle:
      VLookup = \
        CgiUtil.ParseString(os.environ["TMDA_VLOOKUP"], User )
      List = Util.RunTask(VLookup[1:])
      Sandbox = {"User": User}
      Filename = os.path.join("stubs", "%s.py" % VLookup[0])
      try:
        execfile(Filename, Sandbox)
      except IOError:
        CgiUtil.TermError("Can't load virtual user stub.",
          "Cannot execute %s" % Filename, "execute stub",
          "TMDA_VLOOKUP = %s" % os.environ["TMDA_VLOOKUP"],
          """Contact this message's sender by an alternate means and inform them
of this error, or try confirming your message using an alternate method.""")
      Home, UID, GID = Sandbox["getuserparams"](List)[0:3]
    else:
      Home, UID, GID = Util.getuserparams(pwd.getpwuid(UID)[0])
  except KeyError:
    CgiUtil.TermError("No such user", "User %s not found" % User, 
      "find user %s" % User, "", 
      """Contact this message's sender by an alternate means and inform them
of this error, or try confirming your message using an alternate method.""")
  if UID < 2:
    PasswordRecord = pwd.getpwnam(os.environ["TMDA_VUSER"])
    UID = PasswordRecord[2]
    GID = PasswordRecord[3]
    if not int(UID):
      CgiUtil.TermError("TMDA_VUSER is UID 0.", "It is not safe to run "
        "tmda-cgi as root.", "set euid",
        "TMDA_VUSER = %s" % os.environ["TMDA_VUSER"],
        """Contact this message's sender by an alternate means and inform them
of this error, or try confirming your message using an alternate method.""")

  # We now have the home directory and the User.  Set this in the environment.
  os.environ["USER"] = User
  os.environ["LOGNAME"] = User
  os.environ["HOME"] = Home

  # Is there a TMDARC variable?
  if os.environ.has_key("TMDARC"):
    # Yes, replace it
    os.environ["TMDARC"] = os.environ["TMDARC"].replace("/~/", "/%s/" % User)

  # Try to change users
  try:
    os.seteuid(0)
    os.setegid(0)
    os.setgid(int(GID))
    os.setuid(int(UID))
  except OSError:
    pass

  # Now that we know who we are, get our defaults
  try:
    from TMDA import Defaults
  except Errors.ConfigError:
        CgiUtil.TermError("Confirm Failed",
          "Old-style URL is not compatible with virtual users",
          "use incompatible URL", "", """Contact this message's sender by an
alternate means and inform them of this error, or try confirming your message
using an alternate method.""")
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
