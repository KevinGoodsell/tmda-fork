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

"Login page for tmda-cgi."

import os
import CgiUtil
import Template

def Show(Msg = "", Debug = 0):
  "Show a login form in HTML."

  try:
    T = Template.Template("login.html")
  except IOError:
    CgiUtil.TermError("Cannot access templates.", "Have Python library files "
      "been moved from where they were unzipped?", "reading templates",
      CgiUtil.FileDetails("default theme directory",
      Template.Template.Dict["ThemeDir"]), "Reinstall tmda-cgi.")
  T["LoginErr"] = Msg
  T["Debug"]    = Debug
  print T
