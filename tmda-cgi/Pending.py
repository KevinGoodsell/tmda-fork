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
import re
import Session
import time
import CgiUtil
import Template
from TMDA import Defaults
from TMDA import Pending

# Pre-calc the regular expressions
GoodFN  = re.compile("^\d+\.\d+\.msg$")
Address = re.compile("^(.+) +<.+>")

def Show():
  "Show all pending e-mail in an HTML form."

  if Form.has_key("subcmd"):
    # Batch operation
    if Form["subcmd"].value == "batch":
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
  Queue = Pending.Queue(cache = 1)
  Queue.initQueue()
  Queue._loadCache()
  Msgs = Queue.listPendingIds()
  
  # Any messages no longer "in process"?
  for PMsg in PVars["InProcess"].keys()[:]:
    try:
      Msgs.index(PMsg)
    except ValueError:
      del PVars["InProcess"][PMsg]

  # Load the display template
  T = Template.Template("pending.html")
  
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
    T["DispRange"] = "%d-%d of %d" % (FirstMsg + 1, LastMsg, len(Msgs))
  else:
    T["DispRange"] = ""
  
  # Update session
  PVars["Pager"] = FirstMsg
  PVars.Save()

  # Capture extra radio buttons. If not present, remove icon
  NumCols = 7
  NumBlankCols = 3
  WhRadio = T["WhRadio"]
  BlRadio = T["BlRadio"]
  if not Defaults.PENDING_WHITELIST_APPEND:
    T["WhIcon"]
  else:
    NumCols += 1
    NumBlankCols += 1
  if not Defaults.PENDING_BLACKLIST_APPEND:
    T["BlIcon"]
  else:
    NumCols += 1
    NumBlankCols += 1
  T["NumCols"] = NumCols
  T["NumBlankCols"] = NumBlankCols

  # Javascript confirmation?
  if Defaults.CGI_USE_JS_CONFIRM:
    T["OnSubmit"] = 'onSubmit="return TestConfirm()"'
    T["ConfirmScript"] = """<script>
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

  # Parse out embedded variables from template
  Row          = T["Row"]
  InProcessRow = T["InProcessRow"]
  InProcess    = T["InProcess"]
  if len(Msgs):
    # Add rows for messages if there are any
    Count = 0
    InProcMsg = ""
    for Msg in Msgs[FirstMsg:LastMsg]:
      T["MsgID"] = Msg
      
      # Print a single message record inside list loop
      try:
        MsgObj = Pending.Message(Msg)
      except IOError:
        pass
  
      # Message size
      T["Size"] = CgiUtil.Size(MsgObj.msgobj)
  
      # Find preferred date
      T["Date"] = time.strftime \
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
      T["Subject"] = Subject
      
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
      T["Sender"] = From
      
      if PVars["InProcess"].has_key(Msg):
        InProcess.Clear()
        InProcess.Add()
        InProcessRow.Add()
      else:
        # Message is not "in process"
        T["RadioName"] = "a%d" % Count
        T["MsgName"]   = "m%d" % Count
        T["MsgID"]     = Msg

        # Read this one yet?
        if Msg in Queue.msgcache:
          T["MsgClass"] = "OldMsg"
        else:
          T["MsgClass"] = "NewMsg"

        if Defaults.PENDING_WHITELIST_APPEND:
          WhRadio.Clear()
          WhRadio.Add()
        if Defaults.PENDING_BLACKLIST_APPEND:
          BlRadio.Clear()
          BlRadio.Add()

      Row.Add()
      Count = Count + 1
  
  # No messages to display
  else:
    T["Row"] = '<tr><td colspan="4" class="InProcess"><i>None.</i></td></tr>'

  print T
