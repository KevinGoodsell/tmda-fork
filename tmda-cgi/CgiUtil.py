#!/usr/bin/env python
#
# Copyright (C) 2002 Gre7g Luterman <gre7g@wolfhome.com>
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

"Utilities for tmda-cgi."

import cgi
import os
import sys
import time

# Handy values
DispDir = os.environ["TMDA_CGI_DISP_DIR"]

def Size(MsgObj):
  MsgSize = len(MsgObj.as_string())
  if MsgSize > 512:
    if MsgSize > 5120:
      if MsgSize > 524288:
        if MsgSize > 5242880:
          MsgSize = "%dM" % (MsgSize / 1048576)
        else:
          MsgSize = "%3.1fM" % (MsgSize / 1048576.0)
      else:
        MsgSize = "%dk" % (MsgSize / 1024)
    else:
      MsgSize = "%3.1fk" % (MsgSize / 1024.0)
  else:
    MsgSize = "%d" % MsgSize
  return MsgSize

def Escape(s):
  if s:
    return cgi.escape(s)
  return ""

def FileDetails(Desc, Filename):
  try:
    Perm = os.stat(Filename)
    Perm = "%03o" % (Perm[0] & 07777)
  except OSError:
    Perm = "???"
  return "%s file <tt>%s</tt>, permissions %s" % (Desc, Filename, Perm)

def TermError(Err, Cause, Failed, Other, Recommend):
  print """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>tmda-cgi Error</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>

<body>
<p>tmda-cgi cannot continue because a terminal error has been encountered.</p>
<table>
  <tr> 
    <td width="100" valign="top"><b>Error:</b></td>
    <td>%s</td>
  </tr>
  <tr> 
    <td valign="top"><b>Cause:</b></td>
    <td>%s</td>
  </tr>
  <tr> 
    <td valign="top"><b>Additional:</b></td>
    <td>Running in %s mode.<br>
      Attempted to %s with euid %d, egid %d.<br>
      %s
    </td>
  </tr>
  <tr>
    <td valign="top"><b>Recommend:</b></td>
    <td>%s</td>
  </tr>
</table>
</body>
</html>""" % (Err, Cause, os.environ["TMDA_CGI_MODE"], Failed, os.geteuid(),
  os.getegid(), Other, Recommend)
  sys.exit(0)