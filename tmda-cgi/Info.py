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

import os
import re
import Template
from CgiVersion import All
from TMDA import Version

# Search stuff
AckSearch     = re.compile("^Acknowledgements:")
ContribSearch = re.compile("^Contributions:")
ToDoSearch    = re.compile("^Things left to do:")
IncludeSearch = re.compile("^Includes:")
ItemSearch    = re.compile("^\s+\*\s+(.+)\s+--\s+(.+)")
ContdSearch   = re.compile("^\s+(\s.+)")

def Add(Name, Detail):
  "Add an entry."

  global BugCol

  if Name:
    T["Name"] = Name
    T["Detail"] = Detail
    if Detail == "bug finding":
      BugCell.Add()
      BugCol += 1
      if BugCol == BugCols:
        BugRow.Add()
        BugCell.Clear()
        BugCol = 0
      Name = None
    else:
      Section.Add()

def AddFile(Filename):
  "Add a file to template."

  global BugCol, Section

  # Read file
  F = open(Filename)
  Thanks = F.readlines()
  F.close()

  Section = None
  Name    = None
  Detail  = None
  BugCol  = 0

  for Line in Thanks:
    AckMatch     = AckSearch.search(Line)
    ContribMatch = ContribSearch.search(Line)
    ToDoMatch    = ToDoSearch.search(Line)
    IncludeMatch = IncludeSearch.search(Line)
    ItemMatch    = ItemSearch.search(Line)
    ContdMatch   = ContdSearch.search(Line)
    if AckMatch:
      Add(Name, Detail)
      Section = AckRow
      Name = None
    elif ContribMatch:
      Add(Name, Detail)
      Section = ContRow
      Name = None
    elif ToDoMatch:
      Add(Name, Detail)
      Section = ToDoRow
      Name = None
    elif IncludeMatch:
      Add(Name, Detail)
      Section = IncludeRow
      Name = None
    elif ItemMatch:
      Add(Name, Detail)
      Name = ItemMatch.group(1)
      Detail = ItemMatch.group(2)
    elif ContdMatch:
      Detail += ContdMatch.group(1)
  if Name:
    Add(Name, Detail)
  if BugCol:
    BugRow.Add()

def Show():
  "Show info."

  global T, AckRow, ContRow, ToDoRow, BugCell, BugRow, BugCols, IncludeRow

  # Load the display template
  T = Template.Template("info.html")

  # Fill in variables
  T["CgiVersion"]  = All
  T["TmdaVersion"] = Version.ALL

  # Get rows
  ParamRow   = T["Params"]
  AckRow     = T["AckRow"]
  ContRow    = T["ContRow"]
  ToDoRow    = T["ToDoRow"]
  BugCell    = T["BugCell"]
  BugRow     = T["BugRow"]
  BugCols    = int(T["BugCols"])
  IncludeRow = T["IncludeRow"]

  # Add compile parameters
  os.environ["TMDA_IDs"] = "UID: %d (%d) GID: %d (%d)" % (os.getuid(),
    os.geteuid(), os.getgid(), os.getegid())
  Keys = os.environ.keys()
  Keys.sort()
  for Param in Keys:
    if Param[:5] == "TMDA_":
      T["Name"]   = Param[5:]
      T["Detail"] = os.environ[Param]
      ParamRow.Add()

  # Add Acknowledgements, Contributions, & ToDo's
  AddFile("THANKS")
  AddFile("TODO")

  # Special instructions
  T["Instruct"] = PVars[("NoOverride", "InstallInstruct")]

  # Display template
  print T
