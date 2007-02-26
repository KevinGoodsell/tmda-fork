#!/usr/bin/env python
#
# Copyright (C) 2003 John Maslanik <maz@mlx.net>
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

"Stub for interfacing to vmailmgr"

def getuserparams(List):
  for Line in List:
    Parts = Line.split(":")
    if (Parts[0] == User):
      return ':'.join(Parts[1:-2]), Parts[-2], Parts[-1]

  # User does not exist
  raise KeyError
