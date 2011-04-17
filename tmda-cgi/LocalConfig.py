#!/usr/bin/env python
#
# Copyright (C) 2003 Gre7g Luterman <gre7g@wolfhome.com>
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

"Local config file editor for tmda-cgi."

import re

import CgiUtil
import Template

from TMDA import Defaults

def Show():
  "Edit local config file."

  # Load the display template
  T = Template.Template("localconfig.html", PVars = PVars)
  T["ErrMsg"] = "Displaying config file editing form."
  ErrStr = None

  # Get file
  T["FilePath"] = Defaults.TMDARC
  try:
    F = open(Defaults.TMDARC)
    FileContents = F.read()
    F.close()
  except IOError:
    FileContents = ""

  T["FileContents"] = FileContents

  # Hide save button?
  if PVars[("NoOverride", "MayEditLocalConfig")][0].lower() == "n":
    T["SaveButton"]

  # Saving with text method?
  if (Form.has_key("subcmd") and Form["subcmd"].value == "save" and
    PVars[("NoOverride", "MayEditLocalConfig")][0].lower() == "y"):
    try:
      # Make sure the list is properly formatted
      Config = re.sub("\r\n", "\n", Form["config"].value)
      Config = re.sub("\n*$", "", Config)
      Config += "\n"

      # Check code for syntax errors BEFORE saving
      try:
        try:
          exec(Config)
        except (ImportError, NameError):
          pass
        T["ErrRow"]
        F = open(Defaults.TMDARC, "w")
        F.write(Config)
        F.close()
      except SyntaxError, (ErrStr, Details):
        T["ErrStr"] = "SyntaxError: line %d, char %d<br>(%s)" % Details[1:4]
      T["FileContents"] = Config
    except IOError, ErrStr:
      CgiUtil.TermError("Unable to save config file.",
      "Insufficient privileges", "save config", "%s<br>%s" % (ErrStr,
      CgiUtil.FileDetails("Local config", Defaults.TMDARC)),
      "Change file permissions on <tt>%s</tt>" % Defaults.TMDARC)

  # Did we find any errors?
  if ErrStr:
    T["PathRow"]  # Hide path
  else:
    T["ErrRow"]   # Hide error

  # Display template
  print T
