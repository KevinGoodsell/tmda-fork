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
  Pending.Show()
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

# Prepare the traceback in case of uncaught exception
MyCgiTb.Content()
MyCgiTb.ErrTemplate = "prog_err.html"

# Make some global stuff available to all
Template.Template.BaseDir = "%s/themes/Blue/template" % \
  os.environ["TMDA_CGI_DISP_DIR"]
Template.Template.Dict["Script"]  = os.environ["SCRIPT_NAME"]
Template.Template.Dict["DispDir"] = os.environ["TMDA_CGI_DISP_DIR"]
Template.Template.Dict["ThemeDir"] = "%s/themes/Blue" % \
  os.environ["TMDA_CGI_DISP_DIR"]

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
    # Initial, non-debug login
    import Login
    Login.Show()

  # Logged in yet?
  elif not PVars.has_key("UID"):
    import Login
    if Form.has_key("cmd"):
      Login.Show("Wrong password.")
    else:
      if Form.has_key("debug"):
        Login.Show(Debug = Form["debug"].value)

  elif Form.has_key("cmd"):
    # Just log in?
    if Form.has_key("user"):
      PVars["SortDir"]   = "desc"
      PVars["Pager"]     = 0
      PVars["Headers"]   = "short"
      PVars["InProcess"] = {}
      PVars.Save()
      
    import Pending
    import View
    
    # Share "globals"
    Pending.PVars = PVars
    Pending.Form  = Form
    View.PVars    = PVars
    View.Form     = Form
    CgiUtil.PVars = PVars
    
    # View?
    if Form["cmd"].value == "list":
      Pending.Show()
    elif Form["cmd"].value == "view":
      if Form.has_key("msgid"):
        PVars["MsgID"] = Form["msgid"].value
      if Form.has_key("headers"):
        PVars["Headers"] = Form["headers"].value
      PVars.Save()
      View.Show()

  else: print "No command.<p>"

  #print "<hr> Everything below this line is experimental.<p>"
  #cgi.print_environ()
  #cgi.print_form(Form)
  #cgi.print_form(PVars)

# This is the end my friend.
if __name__ == '__main__':
    main()
