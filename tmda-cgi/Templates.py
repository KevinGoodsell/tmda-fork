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

"Template editor for tmda-cgi."

import os
import re

import CgiUtil
import Template

from TMDA import Defaults

def Show():
  "Edit templates."

  global AssignVar, Assignments, Config, LineNum, LastLine

  # Load the display template
  T = Template.Template("templates.html")
  Row = T["Row"]

  # Hide save button?
  if PVars[("NoOverride", "MayEditTemplates")][0].lower() == "n":
    T["SaveButton"]
  else:
    T["NoSave"]

  if Defaults.TEMPLATE_DIR:
    baseDir = Defaults.TEMPLATE_DIR
  else:
    baseDir = os.environ["TMDA_BASE_DIR"]

  for BaseName in os.listdir( baseDir ):
    if BaseName.endswith( ".txt" ):
      Filename = os.path.join( baseDir, BaseName )

      T["Var"] = BaseName

      # Get file
      T["FilePath"] = Filename
      if CgiUtil.TestTextFilePath(Filename):
        try:
          F = open(Filename)
          FileContents = F.read()
          F.close()
        except IOError:
          FileContents = ""
      else:
        FileContents = "(File is not accessible.)"

      # Saving?
      if Form.has_key("subcmd") and \
        (PVars[("NoOverride", "MayEditTemplates")][0].lower() == "y"):
        try:
          # Make sure the list is properly formatted
          try:
            FileContents = re.sub("\r\n", "\n", Form[BaseName].value)
          except KeyError:
            FileContents = ""
          FileContents = re.sub("\n*$", "", FileContents)
          FileContents += "\n"

          if CgiUtil.TestTextFilePath(Filename):
            F = open(Filename, "w")
            F.write(FileContents)
            F.close()
        except IOError, ErrStr:
          CgiUtil.TermError("Unable to save template file.",
          "Insufficient privileges", "save template", "%s<br>%s" % (ErrStr,
          CgiUtil.FileDetails("Template", Filename)),
          "Change file permissions on <tt>%s</tt>" % Filename)

      T["FileContents"] = FileContents
      Row.Add()

  # Display template
  print T
