#!/usr/bin/env python
#
# Copyright (C) 2003 Jim Ramsay <i.am@jimramsay.com>
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

"Sets up characterset aliases for email.Charset"

import email.Charset

# Aliases to gb2312
for cs in ("csgb2312", "gb_2312-80", "iso-ir-58", "chinese", "csiso58gb231280"):
  email.Charset.add_alias( cs, "gb2312" )

# Aliases to GBK
for cs in ("cp936", "ms936", "windows-936"):
  email.Charset.add_alias( cs, "gbk" )

# Aliases to Big5
for cs in ("big5-hkscs", "csbig5", "chinesebig5"):
  email.Charset.add_alias( cs, "big5" )
