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

"Info for tmda-cgi."

import re
import Template
from Version import All
from TMDA import Version

# Search stuff
AckSearch     = re.compile("^Acknowledgements:")
ContribSearch = re.compile("^Contributions:")
ToDoSearch    = re.compile("^Things left to do:")
ItemSearch    = re.compile("^\s+\*\s+(.+)\s+--\s+(.+)")
ContdSearch   = re.compile("^\s+(\s.+)")

def AddFile(Filename, T, AckRow, ContRow, ToDoRow):
  "Add a file to template."

  # Read file
  F = open(Filename)
  Thanks = F.readlines()
  F.close()
  
  Section = None
  Name    = None
  Detail  = None
  for Line in Thanks:
    AckMatch     = AckSearch.search(Line)
    ContribMatch = ContribSearch.search(Line)
    ToDoMatch    = ToDoSearch.search(Line)
    ItemMatch    = ItemSearch.search(Line)
    ContdMatch   = ContdSearch.search(Line)
    if AckMatch:
      if Name:
        T["Name"] = Name
        T["Detail"] = Detail
        Section.Add()
      Section = AckRow
      Name = None
    elif ContribMatch:
      if Name:
        T["Name"] = Name
        T["Detail"] = Detail
        Section.Add()
      Section = ContRow
      Name = None
    elif ToDoMatch:
      if Name:
        T["Name"] = Name
        T["Detail"] = Detail
        Section.Add()
      Section = ToDoRow
      Name = None
    elif ItemMatch:
      if Name:
        T["Name"] = Name
        T["Detail"] = Detail
        Section.Add()
      Name = ItemMatch.group(1)
      Detail = ItemMatch.group(2)
    elif ContdMatch:
      Detail += ContdMatch.group(1)
  if Name:
    T["Name"] = Name
    T["Detail"] = Detail
    Section.Add()

def Show():
  "Show info."

  # Load the display template
  T = Template.Template("info.html")

  # Fill in variables
  T["CgiVersion"]  = All
  T["TmdaVersion"] = Version.ALL

  # Get rows
  AckRow  = T["AckRow"]
  ContRow = T["ContRow"]
  ToDoRow = T["ToDoRow"]
  
  # Add Acknowledgements, Contributions, & ToDo's
  AddFile("THANKS", T, AckRow, ContRow, ToDoRow)
  AddFile("TODO", T, AckRow, ContRow, ToDoRow)

  # Display template
  print T
