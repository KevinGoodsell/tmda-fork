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

"Stub for interfacing to XAMS."

import MySQLdb
import re

# *** IMPORTANT NOTE: ***
# YOU MUST FILL IN THE FOLLOWING INFORMATION SO THAT THIS STUB MAY CONNECT TO
# MYSQL!!!
DBLogin    = "xams"
DBPassword = ""
DBName     = "xams"

# Other constant
UserFormat   = "(.+)@(.+)"
HomeTemplate = "/var/tmda/%s/%s"

def getuserparams(List):
  # Expects a list of one element, a user name.
  User, Domain = List[0], ""

  # Find the domain
  Match = re.search(UserFormat, User)
  if Match:
    User, Domain = Match.group(1), Match.group(2)
  
  # Connect to MySQL database
  DB = MySQLdb.connect(user = DBLogin, passwd = DBPassword, db = DBName)

  # Query  
  Cursor = DB.cursor()
  Cursor.execute \
  ("""
    SELECT s.name, u.name FROM pm_domains d, pm_sites s, pm_users u
    WHERE s.ID = d.SiteID AND u.SiteID = s.ID AND u.Name = %s AND d.Name = %s
  """, (User, Domain))
  Dir = HomeTemplate % Cursor.fetchone()

  return Dir, 0, 0
