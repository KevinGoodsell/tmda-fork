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

"Pending page for tmda-cgi."

import cgi
import email
import os
import pwd
import re
import Session
import time
import CgiUtil
from TMDA import Defaults
from TMDA import Pending

# Pre-calc the regular expressions
GoodFN  = re.compile("^\d+\.\d+\.msg$")
Address = re.compile("^(.+) +<.+>")

def Show():
  "Show all pending e-mail in an HTML form."

  if Form.has_key("subcmd"):
    # Change sorting direction?
    if Form["subcmd"].value == "desc": PVars["SortDir"] = "desc"
    elif Form["subcmd"].value == "asc":  PVars["SortDir"] = "asc"
    
    # Batch operation
    elif Form["subcmd"].value == "batch":
      for Count in range(Defaults.CGI_PAGER_SIZE):
        if Form.has_key("a%d" % Count):
          # Check to make sure they're not trying to access anything other than 
          # email
          if not GoodFN.search(Form["m%d" % Count].value):
            CgiUtil.TermError("<tt>%s</tt> is not a valid message ID." %
              Form["m%d" % Count].value, "Program error / corrupted link.",
              "retrieve pending e-mail", "",
              "Recheck link or contact TMDA programmers.")
          
          if Form["a%d" % Count].value == "pass": continue
          try:
            MsgObj = Pending.Message(Form["m%d" % Count].value)
            if Form["a%d" % Count].value == "release":
              MsgObj.release()
              PVars["InProcess"][Form["m%d" % Count].value] = 1
            elif Form["a%d" % Count].value == "delete":
              MsgObj.delete()
            elif Form["a%d" % Count].value == "whitelist":
              MsgObj.whitelist()
              MsgObj.release()
              PVars["InProcess"][Form["m%d" % Count].value] = 1
            elif Form["a%d" % Count].value == "blacklist":
              MsgObj.blacklist()
              MsgObj.delete()
          except IOError: pass

  # Locate messages in pending dir
  Queue = Pending.Queue(descending = (PVars["SortDir"] == "desc"), cache = 1)
  Queue.initQueue()
  Queue._loadCache()
  Msgs = Queue.listPendingIds()
  
  # Any messages no longer "in process"?
  for PMsg in PVars["InProcess"].keys()[:]:
    try:
      Msgs.index(PMsg)
    except ValueError:
      del PVars["InProcess"][PMsg]

  # Find the message numbers we'll display
  FirstMsg = PVars["Pager"]
  if Form.has_key("subcmd"):
    if Form["subcmd"].value == "first":  FirstMsg = 0
    elif Form["subcmd"].value == "prev": FirstMsg -= Defaults.CGI_PAGER_SIZE
    elif Form["subcmd"].value == "next": FirstMsg += Defaults.CGI_PAGER_SIZE
    elif Form["subcmd"].value == "last": FirstMsg = len(Msgs)
  if FirstMsg >= len(Msgs): FirstMsg = len(Msgs) - Defaults.CGI_PAGER_SIZE
  if FirstMsg < 0: FirstMsg = 0
  if len(Msgs) <= Defaults.CGI_PAGER_SIZE: FirstMsg = 0
  LastMsg = FirstMsg + Defaults.CGI_PAGER_SIZE
  if LastMsg > len(Msgs): LastMsg = len(Msgs)
  if len(Msgs):
    DisplayRange = "%d-%d of %d" % (FirstMsg + 1, LastMsg, len(Msgs))
  else:
    DisplayRange = ""
  
  # Update session
  PVars["Pager"] = FirstMsg
  PVars.Save()

  # Any extra icons?
  IconWidth = 70
  ExtraIcons = ""
  if Defaults.PENDING_WHITELIST_APPEND:
    IconWidth += 24
    ExtraIcons += "<img src=%ssmwhite.gif width=24 height=19 align=baseline alt='/white'>" \
      % CgiUtil.DispDir
  if Defaults.PENDING_BLACKLIST_APPEND:
    IconWidth += 24
    ExtraIcons += "<img src=%ssmblack.gif width=24 height=19 align=baseline alt='/black'>" \
      % CgiUtil.DispDir

  # Sort direction?
  if PVars["SortDir"] == "asc":
    SortIcon   = "<img src=%sup.gif width=11 height=13 alt='Sorted Ascending'>" \
      % CgiUtil.DispDir
    ToggleSort = "desc"
  else:
    SortIcon   = "<img src=%sdown.gif width=11 height=13 alt='Sorted Descending'>" \
      % CgiUtil.DispDir
    ToggleSort = "asc"

  # NavBar HTML (since it is displayed twice)
  NavBarHTML = """  <tr align="center" class="NavBar">
    <td width="25%%"><a href="%(script)s?cmd=list&subcmd=first&SID=%(SID)s"><img alt="First"
      src="%(dir)sfirst.gif" width="24" height="42" border="0"></a></td>
    <td width="25%%"><a href="%(script)s?cmd=list&subcmd=prev&SID=%(SID)s"><img alt="Prev"
      src="%(dir)sprev.gif" width="21" height="42" border="0"></a></td>
    <td width="25%%"><a href="%(script)s?cmd=list&subcmd=next&SID=%(SID)s"><img alt="Next"
      src="%(dir)snext.gif" width="21" height="42" border="0"></a></td>
    <td width="25%%"><a href="%(script)s?cmd=list&subcmd=last&SID=%(SID)s"><img alt="Last"
      src="%(dir)slast.gif" width="24" height="42" border="0"></a></td>
  </tr>""" % {"script": os.environ["SCRIPT_NAME"], "SID": PVars.SID,
    "dir": CgiUtil.DispDir}

  print """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>Pending E-mails for %s</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<link href="%sstyles.css" rel="stylesheet" type="text/css">""" % \
    (Defaults.FULLNAME, CgiUtil.DispDir)
  
  if Defaults.CGI_USE_JS_CONFIRM:
    print """<script>
function TestConfirm()
{
  ToBlacklist = 0
  ToDelete = 0
  for (i = 0; i < %s; i++)
  {
    action = document.forms.actions["a" + i]
    if (action)
      for (j = 0; j < action.length; j++)
      {
        if (action[j].checked && (action[j].value == "blacklist")) ToBlacklist++
        if (action[j].checked && (action[j].value == "delete")) ToDelete++
      }
  }
  if (ToDelete)
    if (ToBlacklist) Msg = "Permanently delete and blacklist"
    else Msg = "Permanently delete"
  else
    if (ToBlacklist) Msg = "Permanently blacklist"
    else return true
  if ((ToDelete + ToBlacklist) == 1) Msg += " this pending message?"
  else Msg += " these pending messages?"
  if (ToDelete) Msg += "\\nAny confirmation that follows will fail."
  return confirm(Msg)
}
</script>""" % Defaults.CGI_PAGER_SIZE

  print """</head>

<body class="PendingPage">
<table>"""
  
  if len(Msgs): print """%s
  <tr>
    <td colspan="4">
      <hr class=NavDiv>
    </td>
  </tr>""" % NavBarHTML
  
  print """  <tr class="Heading">
    <td colspan="3">Incoming e-mails still pending delivery:</td>
    <td align="right">%s</td>
  </tr>""" % DisplayRange
  
  if len(Msgs):
    # Display pending messages if there are any
    if Defaults.CGI_USE_JS_CONFIRM:
      print "  <form method=post action=%s name=actions onSubmit='return TestConfirm()'> " \
        % os.environ["SCRIPT_NAME"]
    else:
      print "  <form method=post action=%s name=actions>" % os.environ["SCRIPT_NAME"]
      
    print """    <tr>
      <td colspan="4">
        <table class="MailList">
          <tr> 
            <td width="%d" nowrap><img src="%sactions.gif" width="66" height="19"
      align="baseline" alt="leave/release/delete">%s</td>
            <th width="150"><a href="#">Sender</a></th>
            <th width="250"><a href="#">Subject</a></th>
            <th width="80"><a href="%s?cmd=list&subcmd=%s&SID=%s">Date</a> %s</th>
            <th width="50"><a href="#">Size</a></th>
          </tr>
          <tr bgcolor="#CCCCCC"> 
            <td colspan="5" class="Spacer"></td>
          </tr>
""" % (IconWidth, CgiUtil.DispDir, ExtraIcons, os.environ["SCRIPT_NAME"],
       ToggleSort, PVars.SID, SortIcon)

    Count = 0
    InProcMsg = ""
    for Msg in Msgs[FirstMsg:LastMsg]:
      # Print a single message record inside list loop
      try:
        MsgObj = Pending.Message(Msg)
      except IOError:
        pass
  
      # Message size
      MsgSize = CgiUtil.Size(MsgObj.msgobj)
  
      # Find preferred date
      Date = time.strftime \
      (
        Defaults.CGI_DATE_FORMAT,
        time.localtime(int(MsgObj.msgid.split('.')[0]))
      )
  
      # Subject:
      if not MsgObj.msgobj["subject"]:
        Subject = "None"
      else:
        Subject = MsgObj.msgobj["subject"]
        if len(Subject) > Defaults.CGI_CROP_SUBJECT:
          Subject = \
            cgi.escape(Subject[:Defaults.CGI_CROP_SUBJECT - 1]) + "&#8230;"
        else:
          Subject = cgi.escape(Subject)
      
      # From:
      if not MsgObj.msgobj["from"]:
        From = ""
      else:
        From = MsgObj.msgobj["from"]
        Temp = Address.search(From)
        if Temp:
          From = Temp.group(1)
      if len(From) > Defaults.CGI_CROP_SENDER:
        From = \
          cgi.escape(From[:Defaults.CGI_CROP_SENDER - 1]) + "&#8230;"
      else:
        From = cgi.escape(From)
      
      if PVars["InProcess"].has_key(Msg):
        # Message is "in process"
        print """          <tr class="InProcess"> 
            <td></td>
            <td>%s</td>
            <td>%s</td>""" % (From, Subject)
        InProcMsg = """<table>
  <tr>
    <td class="Note">Note:</td>
    <td>
      <span class="InProcess">Marked</span> messages are being processed by the 
      mail server.<br>
      They will be removed from the pending list when released.
    </td>
  </tr>
</table>"""
      else:
        # Message is not "in process"

        # Read this one yet?
        if Msg in Queue.msgcache:
          print "<tr class=OldMsg>"
        else:
          print "<tr class=NewMsg>"

        print """            <td nowrap>
              <table cellpadding="0" cellspacing="0" border="0">
                 <tr>
         <td width=24><input name="a%d" type="radio" value="pass" checked></td>
         <td width=24><input name="a%d" type="radio" value="release"></td>
         <td width=24><input name="a%d" type="radio" value="delete"></td>""" \
          % (Count, Count, Count)
    
        if Defaults.PENDING_WHITELIST_APPEND:
          print "<td width=24><input name=a%d type=radio value=whitelist></td>" \
            % Count
        if Defaults.PENDING_BLACKLIST_APPEND:
          print "<td width=24><input name=a%d type=radio value=blacklist></td>" \
            % Count
      
        print """              <input type=hidden name=m%d value='%s'>
                </tr>
              </table>
            </td>
            <td>%s</td>
            <td><a href="%s?cmd=view&msgid=%s&SID=%s">%s</a></td>""" % \
          (Count, Msg, From, os.environ["SCRIPT_NAME"], Msg, PVars.SID,
          Subject)
      
      # Finish message record regardless of whether it is "in process"
      print """            <td nowrap>%s</td>
            <td>%s</td>
          </tr>
          <tr bgcolor="#CCCCCC"> 
            <td colspan="5" class="Spacer"></td>
          </tr>""" % (Date, MsgSize)
      Count = Count + 1
      # (end of) Print a single message record inside list loop

    print """          <tr> 
            <td valign="top"><input type="submit" class="gobutton" value="Go"></td>
            <td colspan="4">%s</td>
          </tr>
        </table>
        <hr class=NavDiv>
      </td>
      <input type="hidden" name="cmd" value="list">
      <input type="hidden" name="subcmd" value="batch">
      <input type="hidden" name="SID" value="%s">
    </tr>
  </form>
%s""" % (InProcMsg, PVars.SID, NavBarHTML)
    # (end of) Display pending messages if there are any
  
  # No messages to display
  else:
    print "<tr><td colspan=4><i>None.</i></td></tr>"

  print """</table>
</body>
</html>"""
