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

"Password checker for tmda-cgi."

import CgiUtil
import crypt
import os
import os.path
import pwd
import random

def ComparePassword(Filename, User, Password):
  """Checks password against a given filename.

Returns:
   1: File read, user found, password authenticated
   0: File read, user found, login deactivated
  -1: File read, user found, password wrong
  -2: File read, user not found
  -3: File couldn't be read"""
  try:
    F = open(Filename) 
  except IOError:
    return -3

  RetVal = -2
  while (1):
    PasswordRecord = F.readline()

    # End of file?
    if PasswordRecord == "":
      break
    Temp = PasswordRecord.strip().split(":")

    # Have we found the correct user record?
    if Temp[0] == User:
      if Temp[1] == "":
        RetVal = 0
        break
      
      Perm = os.stat(Filename)[0] & 07777

      # Is the password in the file encrypted?
      if (Perm != 0400) and (Perm != 0600):
        if crypt.crypt(Password, Temp[1][:2]) == Temp[1]:
          RetVal = 1
        else:
          RetVal = -1
        break
      else:
        if Temp[1] == Password:
          RetVal = 1
        else:
          RetVal = -1
        break
  F.close()
  return RetVal

def CheckPassword(Form):
  "Checks a password against password files."

  try:
    # Find the requested home directory
    os.environ["HOME"] = pwd.getpwnam(Form["user"].value)[5]

    # Look in same directory as TMDARC file
    if os.environ.has_key("TMDARC"):
      # Given location?
      FN = os.path.join(os.path.split(os.environ["TMDARC"])[0], "tmda-cgi")
    else:
      # No given location, try ~/.tmda/tmda-cgi
      FN = os.path.expanduser("~/.tmda/tmda-cgi")
  
    # Login succeed?
    RetVal = ComparePassword(FN, Form["user"].value, Form["password"].value)
    if RetVal > 0:
      return RetVal
  except KeyError:
    RetVal = -4
    FN = "<i>n/a</i>"
  
  # Login help?
  if int(Form["debug"].value):
    Errors = ["Logins for user %(user)s have been deactivated in file <tt>%(file)s</tt>",
      "Password incorrect for user %(user)s in file <tt>%(file)s</tt>",
      "User %(user)s was not found in file <tt>%(file)s</tt>",
      "Could not read file <tt>%(file)s</tt>",
      "User %(user)s does not exist"]
    Err = Errors[-RetVal] % {"user": Form["user"].value, "file": FN}
    Err += "<br>" + CgiUtil.FileDetails("Local password", FN)
    if RetVal > -2:
      CgiUtil.TermError("Login failed", "Bad pass / login disabled.", "validate password",
        Err, "Correct entry for %s in file <tt>%s</tt>" % (Form["user"].value, FN))
  if RetVal > -2:
    return RetVal

  # Login succeed?
  FN = "/etc/tmda-cgi"
  try:
    RetVal = ComparePassword(FN, Form["user"].value, Form["password"].value)
  except KeyError:
    RetVal = -4
  if RetVal > 0:
    return RetVal

  # Login help?
  if int(Form["debug"].value):
    Err += "<br>" + Errors[-RetVal] % {"user": Form["user"].value, "file": FN}
    Err += "<br>" + CgiUtil.FileDetails("Global password", FN)
    CgiUtil.TermError("Login failed", "Password / password file error.",
      "validate password", Err, "Reset password or correct file permissions")
  return RetVal
  