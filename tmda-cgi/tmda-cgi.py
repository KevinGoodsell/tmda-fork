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

"""Web interface to TMDA tools.

This program is expected to be called as a CGI.  See htdocs/tmda-cgi.html for
specific instructions on using this file.

Fields:
  Login.Show(Msg)
    Form:  None
    PVars: None
  PendList.Show()
    Form:  [user, password], cmd=view, [subcmd=first|prev|next|last|batch]
           [a#=X|r|d|w|b, m#]
    PVars: UID, GID, User, HOME, SortDir, Pager
  View.Show()
    Form:  cmd=view, [subcmd=first|prev|next|last|delete|release|white|black],
           [headers=short|all], [msgid]
    PVars: UID, GID, User, HOME, Headers, MsgID
"""

import cgi
import os
import sys

sys.path.insert(0, os.environ["TMDA_BASE_DIR"])
import CgiUtil
import MyCgiTb
import Session
import Template

from TMDA import Errors

# Prepare the traceback in case of uncaught exception
MyCgiTb.Content()
MyCgiTb.ErrTemplate = "prog_err.html"

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
PVars = Session.Session(Form)

def main():
  "Figure out which page we're on and pass control along."

  # First visit to any page?
  if not Form.keys():
    # Release an e-mail by URL?
    try:
      if os.environ["QUERY_STRING"]:
        import Release
        Release.Release(os.environ["QUERY_STRING"])
        return
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
    # Just log in?
    if Form.has_key("user"):
      PVars["Pager"]     = 0
      PVars["InProcess"] = {}
      PVars.Save()
      
    import GenAddr
    import GlobalConfig
    import PendList
    import Theme
    import View
    
    # Share "globals"
    CgiUtil.PVars  = PVars
    GenAddr.PVars  = PVars
    GenAddr.Form   = Form
    PendList.PVars = PVars
    PendList.Form  = Form
    Theme.PVars    = PVars
    Theme.Form     = Form
    View.PVars     = PVars
    View.Form      = Form
    
    # View?
    if Form["cmd"].value == "pending":
      PendList.Show()
    elif Form["cmd"].value == "view":
      try:
        View.Show()
      except Errors.MessageError:  # No messages left?
        PendList.Show()
    elif Form["cmd"].value == "theme":
      Theme.Show()
    elif Form["cmd"].value == "globalconfig":
      GlobalConfig.Show()
    elif Form["cmd"].value == "gen_addr":
      GenAddr.Show()
    else:
      CgiUtil.TermError("Command not recognized.", "Unknown command: %s" %
        Form["cmd"].value, "interpret command", "", "Please be patient while "
        "we release newer versions of the code which will implement this "
        "function.")

  else:
    CgiUtil.TermError("No command instruction.", "Program bug.",
      "interpret command", "", "Please contact the programmers and let them "
      "know what you did to reach this message.")

  #print "<hr> Everything below this line is experimental.<p>"
  #cgi.print_environ()
  #cgi.print_form(Form)
  #cgi.print_form(PVars)

# This is the end my friend.
if __name__ == '__main__':
    main()
