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

"Stub for interfacing to vpopmail."

import re

# Constants
Matcher = re.compile("^([^:]+):\s*(\S.*?)\s*$")

def getuserparams(List):
  # Convert a list returned by vuserinfo into a dictionary
  Dict = {"uid": "0", "gid": "0", "gecos": None}
  for Line in List:
    Match = Matcher.search(Line)
    if Match:
      Dict[Match.group(1)] = Match.group(2)

  # Return the home directory, UID, and GID
  return Dict["dir"], 0, 0, Dict["gecos"]
