#!/usr/bin/env python2
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

import pwd
import re
import string
import cdb
import vmailmgr
import sys
import os

# Constants
UserFormat = "(.+)@(.+)"

# Config
QVirtFile = "/var/qmail/control/virtualdomains"

# return vuser
def GetQmailVuser(Domain):
  infile = open(QVirtFile,'r')
  for line in infile.readlines():
    line = string.rstrip(line)
    field = string.split(line,':')
    if(field[0] == Domain):
      return field[1]
  return ""

# Expects a list of one element, a user name.
User, Domain = sys.argv[1], ""

# Find the domain
Match = re.search(UserFormat, User)

IncDomainName = 0

if Match:
  User, Domain = Match.group(1), Match.group(2)
  IncDomainName = 1
else:
  if os.environ.has_key("HTTP_HOST"):
    Domain = os.environ["HTTP_HOST"]

SysUser = GetQmailVuser(Domain)

if SysUser:
  Pwent = pwd.getpwnam(SysUser)
  SysHomeDir = Pwent[5]
  Uid = Pwent[2]
  Gid = Pwent[3]
else:
  Pwent = pwd.getpwnam(User)
  SysHomeDir = Pwent[5]
  Uid = Pwent[2]
  Gid = Pwent[3]
  print User + ":" + SysHomeDir + ":" +  str(Uid) + ":" + str(Gid)
  sys.exit(0)

VFile = SysHomeDir + "/passwd.cdb"
Vpasswd = cdb.init(VFile)
Vpwent = Vpasswd.get(User)

if Vpwent:
  Vuser = vmailmgr.types.VUser()
  Vmgr = Vuser.from_binary(Vpwent)
  DirPart = Vuser.mailbox
  Dir = SysHomeDir + DirPart.lstrip(".")
  if IncDomainName:
    print User + '@' + Domain + ":" + Dir + ":" +  str(Uid) + ":" + str(Gid)
  else:
    print User + ":" + Dir + ":" +  str(Uid) + ":" + str(Gid)
else:
  sys.exit(0)

