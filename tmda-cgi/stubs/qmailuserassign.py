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

"Stub for interfacing to /var/qmail/users/assign"

def getuserparams(List):
  # Find correct item and convert a list returned by
  # "/bin/cat /var/qmail/users/assign" into a dictionary
  Dict = {}
  Proximity = -1
  for Line in List:
    Parts = Line[1:].split(":")
    if (Line[0] == "=") and (Parts[0] == User):
      return Parts[4], Parts[2], Parts[3]

  # User does not exist
  raise KeyError
