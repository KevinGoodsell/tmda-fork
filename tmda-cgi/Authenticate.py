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
import random
import socket
import sys

import Template
from TMDA import Auth
from TMDA import Errors
from TMDA import Util

DebugStringOutput = Util.StringOutput()
authobj = Auth.Auth( debugObject = DebugStringOutput )

authinit = 0

def InitProgramAuth( Program ):
  """Initializes the authentication scheme with a checkpw-style program.
    (Implemented by Auth.py)"""

  # Populate TCPLOCALHOST for checkpw-stype programs that need it
  # (i.e. checkvpw)
  if os.environ.has_key("HTTP_HOST"):
    os.putenv('TCPLOCALHOST',os.environ["HTTP_HOST"])

  global authinit
  authinit = 0
  try:
    authobj.init_auth_method( 'checkpw', Program )
    authinit = 1
  except ValueError, verr:
    raise verr

def InitFileAuth( Filename="/etc/tmda-cgi" ):
  """Initializes the authentication scheme with a flat file
    (Implemented by Auth.py)"""
  global authinit
  authinit = 0
  try:
    authobj.init_auth_method( 'file', Filename )
    authinit = 1
  except ValueError, verr:
    raise verr

def InitRemoteAuth( URI ):
  """Initialaze the authentication scheme with a remote URL
    (Implemented by Auth.py)"""
  global authinit
  authinit = 0
  try:
    authobj.init_auth_method( 'remote', URI )
    authinit = 1
  except ValueError, verr:
    raise verr

def Authenticate(User, Password):
  """Checks password against initialized authentication scheme filename.

 - Returns 1 or 0, depending on authentication.

 - May raise Errors.AuthError if something "funny" happens."""
  global authinit
  RetVal = 0
  if authinit:
    try:
      RetVal = authobj.authenticate_plain( User, Password )
    except Errors.AuthError, error:
      raise error
  else:
    raise Errors.AuthError, "No authentication mechanism initialized."
  # If we made it this far, we're either returning 1 or 0.
  return RetVal

def CheckPassword(Form):
  "Checks a password from a form."
  global DebugStringOutput

  Except = ""
  try:
    RetVal = Authenticate( Form["user"].value, Form["password"].value )
  except Errors.AuthError, error:
    Except = "\n*** EXCEPTION CAUGHT ***: %s" % error.msg
    RetVal = 0
  except socket.error, (error, msg):
    Except = "\n*** EXCEPTION CAUGHT ***: %s" % msg
    RetVal = 0
  Template.Template.Dict["ErrMsg"] = "Capturing the debug stream...\n" + \
    DebugStringOutput.__repr__() + Except

  return RetVal
