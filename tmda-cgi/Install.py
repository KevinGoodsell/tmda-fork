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

"Global config file viewer for tmda-cgi."

import os
import Template

def Show():
  "Handle installation."

  # Load the display template
  if Form["cmd"].value == "conf-example":
    TemplateFN = "conf-example.html"
  elif Form["cmd"].value == "faq":
    TemplateFN = "faq.html"
  elif Form["cmd"].value == "install":
    TemplateFN = "installed.html"
  elif Form["cmd"].value == "welcome":
    TemplateFN = "welcome.html"
  else:
    # Have they installed before?
    if os.access(os.path.join(os.environ["HOME"],
      PVars[("NoOverride", "UninstallBackupTGZ")]), os.R_OK):
      TemplateFN = "re-enroll.html"
    else:
      TemplateFN = "welcome.html"

  # Display template
  T = Template.Template(TemplateFN)
  print T
