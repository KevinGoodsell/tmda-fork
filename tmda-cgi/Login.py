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

"Login page for tmda-cgi."

import os
import CgiUtil

def Show(Msg = "Please enter your login information.", Debug = 0):
  "Show a login form in HTML."

  print """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>TMDA Login</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<link href="%sstyles.css" rel="stylesheet" type="text/css">
</head>

<body class="LoginPage">
<table width="100%%" height="100%%">
  <tr>
    <td align="center">
      <form method="post" action="%s" name="login">
        <table cellpadding="15" class="LoginOuter">
          <tr> 
            <td align="center">%s
              <p> 
              <table class="LoginInner" width="250">
                <tr> 
                  <td align="right">User:</td>
                  <td><input name="user" type="text" id="user" size="6"></td>
                </tr>
                <tr> 
                  <td align="right">Password:</td>
                  <td><input name="password" type="password" id="password" size="6"></td>
                </tr>
                <tr align="center" valign="bottom"> 
                  <td height="25" colspan="2">
                    <input type="hidden" name="cmd" value="list">
                    <input type="submit" value="Login" class="LoginButton">
                    <input type="hidden" name="debug" value="%s">
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </form>
      <script>
        document.forms[0].user.focus()
      </script>
    </td>
  </tr>
</table>
</body>
</html>
""" % (CgiUtil.DispDir, os.environ["SCRIPT_NAME"], Msg, Debug)
