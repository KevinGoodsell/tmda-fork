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

"Web interface to TMDA tools."

import cgi
import os
import sys

# Pick up the TMDA and TMDA/pythonlib directories to get any overrides of
# standard modules and packages.  Note that these must go at the very front of
# the path for this reason.
sys.path.insert(0, os.environ["TMDA_BASE_DIR"])
sys.path.insert(0, os.path.join(os.environ["TMDA_BASE_DIR"], "TMDA",
  "pythonlib"))
from TMDA import Errors

import CgiUtil
import MyCgiTb
import Session
import Template

# Prepare the traceback in case of uncaught exception
MyCgiTb.Content()
MyCgiTb.ErrTemplate = "prog_err2.html"

# Make some global stuff available to all
Template.Template.BaseDir = "%s/display/themes/Blue/template" % \
  os.path.abspath(os.path.split(sys.argv[0])[0])
Template.Template.Dict["Script"]   = os.environ["SCRIPT_NAME"]
Template.Template.Dict["SID"]      = ""
Template.Template.Dict["DispDir"]  = os.environ["TMDA_CGI_DISP_DIR"]
Template.Template.Dict["ThemeDir"] = "%s/themes/Blue" % \
  os.environ["TMDA_CGI_DISP_DIR"]
Template.Template.Dict["ErrMsg"]   = "No error message returned.  Sorry!"

# Check version information
try:
  import Version
  Version.Test()
except ImportError, ErrStr:
  CgiUtil.TermError("Failed to import TMDA module.", ErrStr, "import TMDA", "",
    "Upgrade to the most recent release of TMDA.")

# Process any CGI fields
Form = cgi.FieldStorage()

# Get any persistent variables
try:
  try:
    PVars = Session.Session(Form)
    CgiUtil.ErrTemplate = "error.html"
  except CgiUtil.NotInstalled, (ErrStr, PVars):
    Template.Template.Dict["ErrMsg"] = ErrStr
    # Can log in but TMDA is not installed correctly
    if ErrStr[0].find("must be chmod 400 or 600") < 0:
      # Serious error.  Suggest an install
      import Install
      Install.Form  = Form
      Install.PVars = PVars
      Install.Show()
      sys.exit()
    else:
      CgiUtil.TermError("crypt_key permissions.", "Bad permissions.",
        "reading crypt_key", ErrStr, "Fix permissions on crypt_key.")
except CgiUtil.JustLoggedIn, (ErrStr, PVars):
  PVars["Pager"]     = 0
  PVars["InProcess"] = {}
  PVars.Save()

# First visit to any page?
if not Form.keys():
  # Release an e-mail by URL?
  try:
    if os.environ["QUERY_STRING"]:
      import Release
      Release.Release(os.environ["QUERY_STRING"])
      sys.exit()
  except KeyError:
    pass
  # Initial login
  import Login
  Login.Show()

# Logged in yet?
elif not PVars.Valid:
  import Login
  if Form.has_key("cmd") and (Form["cmd"].value != "logout"):
    Login.Show("Wrong password.")
  else:
    Login.Show()

elif Form.has_key("cmd"):
  import EditFilter
  import EditList
  import GenAddr
  import GlobalConfig
  import Info
  import Install
  import LocalConfig
  import PendList
  import TestAddr
  import Theme
  import View
  
  # Share "globals"
  CgiUtil.PVars     = PVars
  EditFilter.PVars  = PVars
  EditFilter.Form   = Form
  EditList.PVars    = PVars
  EditList.Form     = Form
  GenAddr.PVars     = PVars
  GenAddr.Form      = Form
  Info.PVars        = PVars
  Install.PVars     = PVars
  Install.Form      = Form
  LocalConfig.PVars = PVars
  LocalConfig.Form  = Form
  PendList.PVars    = PVars
  PendList.Form     = Form
  TestAddr.PVars    = PVars
  TestAddr.Form     = Form
  Theme.PVars       = PVars
  Theme.Form        = Form
  View.PVars        = PVars
  View.Form         = Form
  
  # View?
  if Form["cmd"].value in ("incoming", "outgoing"):
    EditFilter.Show()
  elif Form["cmd"].value[:8] == "editlist":
    EditList.Show()
  elif Form["cmd"].value == "gen_addr":
    GenAddr.Show()
  elif Form["cmd"].value == "globalconfig":
    GlobalConfig.Show()
  elif Form["cmd"].value == "info":
    Info.Show()
  elif Form["cmd"].value == "install":
    pass
  elif Form["cmd"].value == "localconfig":
    LocalConfig.Show()
  elif Form["cmd"].value == "pending":
    PendList.Show()
  elif Form["cmd"].value == "restore":
    pass
  elif Form["cmd"].value == "uninstall":
    Install.Show()
  elif Form["cmd"].value == "view":
    try:
      View.Show()
    except Errors.MessageError:  # No messages left?
      PendList.Show()
  elif Form["cmd"].value == "test_addr":
    TestAddr.Show()
  elif Form["cmd"].value == "theme":
    Theme.Show()
  else:
    CgiUtil.TermError("Command not recognized.", "Unknown command: %s" %
      Form["cmd"].value, "interpret command", "", "Please be patient while "
      "we release newer versions of the code which will implement this "
      "function.")

else:
  CgiUtil.TermError("No command instruction.", "Program bug.",
    "interpret command", "", "Please contact the programmers and let them "
    "know what you did to reach this message.")
