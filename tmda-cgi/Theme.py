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

"Theme picker page for tmda-cgi."

import os
import Template

# Handy stuff
ThemesDir = os.path.join(os.getcwd(), "display", "themes")

def Show():
  "Show all available themes."

  global ThemesDir

  if Form.has_key("subcmd"):
    PVars[("General", "Theme")] = Form["subcmd"].value
    PVars.Save()
    PVars.GetTheme()

  # Load the display template
  T = Template.Template("theme.html")

  # Find the available themes
  Themes = os.listdir(ThemesDir)
  Themes.sort()

  # Extract parts from template
  Selected = T["Selected"]
  Cell     = T["Cell"]
  Row      = T["Row"]
  Columns  = int(T["Columns"])
  NoneLook = T["None"]

  # Add themes to template
  Column = 0
  for Theme in Themes:
    # Skip "CVS" if you see it
    if Theme == "CVS": continue
    
    T["Name"] = Theme
    Selected.Clear()
    if Theme == PVars[("General", "Theme")]:
      Selected.Add()
    Cell.Add()
    Column += 1
    if Column == Columns:
      Row.Add()
      Cell.Clear()
      Column = 0
  if Column: Row.Add()

  # Info about current theme
  T["Name"] = PVars[("General", "Theme")]
  if PVars.has_key(("Theme", "Info")):
    T["Info"] = PVars[("Theme", "Info")]
  else:
    T["Info"] = NoneLook

  # Display template
  print T
