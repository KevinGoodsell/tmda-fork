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

"Filter editor for tmda-cgi."

import os
import re

import CgiUtil
import Template

from TMDA import Defaults

def Show():
  "Edit filter."

  # Load the display template
  if Form["cmd"].value == "incoming":
    T = Template.Template("incoming.html")
    T["FilePath"] = Filename = CgiUtil.ExpandUser(Defaults.FILTER_INCOMING)
  else:
    T = Template.Template("outgoing.html")
    T["FilePath"] = Filename = CgiUtil.ExpandUser(Defaults.FILTER_OUTGOING)

  # Get file
  if CgiUtil.TestTextFilePath(Filename):
    try:
      F = open(Filename)
      T["FileContents"] = F.read()
      F.close()
    except IOError:
      T["FileContents"] = ""
  else:
    T["FileContents"] = "(File is not accessible.)"
  
  # Are we allowed to save?
  if PVars[("NoOverride", "MayEditFilters")][0].lower() == "n":
    T["SaveButton"]
  else:
    # Did they try to save?
    if Form.has_key("subcmd"):

      # Make sure the list is properly formatted
      if Form.has_key("filter"):
        Contents = Form["filter"].value
      else:
        Contents = ""
      Contents = re.sub("\r\n", "\n", Contents)
      Contents = re.sub("\n*$", "", Contents)
      Contents += "\n"

      if CgiUtil.TestTextFilePath(Filename):
        try:
          F = open(Filename, "w")
          F.write(Contents)
          F.close()
          T["FileContents"] = Contents
        except IOError, ErrStr:
          CgiUtil.TermError("Unable to save filter.",
          "Insufficient privileges", "save filter", "%s<br>%s" % (ErrStr,
          CgiUtil.FileDetails("Filter", Filename)),
          "Change file permissions on <tt>%s</tt>" % Filename)
      else:
        FileContents = "(File is not accessible.)"

  # Display template
  print T
