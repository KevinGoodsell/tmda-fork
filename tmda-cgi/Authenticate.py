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
import sys

from TMDA import Auth
from TMDA import Errors

# For now, output all Auth.py errors to http error log
Auth.DEBUGSTREAM = sys.stderr

authinit = 0

def InitProgramAuth( Program, trueProg = "/usr/bin/true" ):
  """Initializes the authentication scheme with a checkpw-style program.
(Implemented by Auth.py)"""
  global authinit
  Auth.authtype = 'prog'
  if not os.access( Program, os.F_OK ):
    authinit = 0
    raise ValueError, "'%s' does not exist" % Program
  if not os.access( trueProg, os.F_OK ):
    authinit = 0
    raise ValueError, "'%s' does not exist", trueProg
  if not os.access( Program, os.X_OK ):
    authinit = 0
    raise ValueError, "'%s' is not executable" % Program
  if not os.access( trueProg, os.X_OK ):
    authinit = 0
    raise ValueError, "'%s' is not executable", trueProg
  # Now initialize the authprog with the checkpasswd program and "true"
  Auth.authprog = "%s %s" % ( Program, trueProg )
  authinit = 1

def InitFileAuth( Filename="/etc/tmda-cgi" ):
  """Initializes the authentication scheme with a flat file
(Not implemented by Auth.py yet)"""
  global authinit
  Auth.authtype = 'file'
  if not os.access( Filename, os.F_OK ):
    authinit = 0
    raise ValueError, "File '%s' does not exist" % Filename
  Auth.authfile = Filename
  authinit = 1

def InitRemoteAuth( URI ):
  """Initialaze the authentication scheme with a remote URL
(Implemented by Auth.py)"""
  global authinit
  Auth.authtype = 'remote'
  try:
    Auth.parse_auth_uri( URI )
    Auth.init_auth_method()
    authinit = 1
  except ValueError, err:
    authinit = 0
    raise Errors.AuthError, "Bad URI: %s" % err.value
  except ImportError, err:
    authinit = 0
    raise Errors.AuthError, "URI scheme not supported: %s" % err.value

def Authenticate(User, Password):
  """Checks password against initialized authentication scheme filename.

 - Returns 1 or 0, depending on authentication.

 - May raise Errors.AuthError if something "funny" happens."""
  global authinit
  RetVal = 0
  if authinit:
    if Auth.authtype == 'prog' or Auth.authtype == 'remote':
      try:
        if Auth.authenticate_plain( User, Password ):
          RetVal = 1
      except Errors.AuthError:
        pass
    elif Auth.authtype == 'file':
      Filename = Auth.authfile
      # Revert to original code since Auth.py doesn't implement files yet.
      try:
        F = open(Filename) 
      except IOError:
        raise Errors.AuthError, \
          "Cannot open file '%s' for reading." % Filename, \
          "Check file permissions"

      PasswordRecord = F.readline()
      while PasswordRecord != "":

        # Split about the :
        Temp = PasswordRecord.strip().split(":")

        # Have we found the correct user record?
        if Temp[0] == User:
          if Temp[1] == "":
            raise Errors.AuthError, \
              "User %s is denied login" % Temp[0], \
              "Blank password in file"

          Perm = os.stat(Filename)[0] & 07777

          # Any file may have encrypted passwords in it.
          # Even though this is a Bad Idea.
          if crypt.crypt(Password, Temp[1][:2]) == Temp[1]:
            RetVal = 1
            break
          # Only <secret> files may have cleartext passwords in it.
          if Perm == 0400 or Perm == 0600:
            if Temp[1] == Password:
              RetVal = 1
              break
        PasswordRecord = F.readline()
      F.close()
    else:
      raise Errors.AuthError, \
        "Authentication mechanism '%s' unknown." % Auth.authtype
  else:
    raise Errors.AuthError, "No authentication mechanism initialized."
  # If we made it this far, we're either returning 1 or 0.
  return RetVal

def CheckPassword(Form):
  "Checks a password from a form."

  errMsg = "Password incorrect for user %s" % Form["user"].value
  errHelp = "Reset password or correct file permissions"
  try:
    if Authenticate( Form["user"].value, Form["password"].value ):
      return 1
  except Errors.AuthError, error:
    errMsg = error.msg
    if error.help != "":
      errHelp = error.help

  if int(Form["debug"].value):
    CgiUtil.TermError("Login failed", "Authentication error",
      "validate password", errMsg, errHelp)
  else:
    return 0
