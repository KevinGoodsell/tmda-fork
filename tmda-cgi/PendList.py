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
import email.Header
import os
import re
import time
import CgiUtil
import Template
import Unicode
from TMDA import Defaults
from TMDA import Errors
from TMDA import Pending

# Pre-calc the regular expressions
GoodFN     = re.compile("^\d+\.\d+\.msg$")
Address    = re.compile("^(.+) +<(.+)>")
ZeroSearch = re.compile("Z-0*(\d)")
ZeroSub    = r"\1"

def Show():
  "Show all pending e-mail in an HTML form."

  ReadList = []
  if Form.has_key("subcmd"):
    # Batch operation
    if Form["subcmd"].value == "batch":
      ReleaseList = [] 
      WhiteList   = []
      BlackList   = []
      DeleteList  = []
      OtherList   = []
      OtherAction = "Pass"
      for Count in range(int(PVars[("PendingList", "PagerSize")])):
        # Check for radioboxes (a0 through a%(PagerSize)d)
        if Form.has_key("a%d" % Count):
          # Check to make sure they're not trying to access anything other than
          # email
          if not GoodFN.search(Form["m%d" % Count].value):
            CgiUtil.TermError("<tt>%s</tt> is not a valid message ID." %
              Form["m%d" % Count].value, "Program error / corrupted link.",
              "process pending e-mail", "",
              "Recheck link or contact TMDA programmers.")

          if Form["a%d" % Count].value == "pass": continue
          try:
            MsgObj = Pending.Message(Form["m%d" % Count].value)
            if Form["a%d" % Count].value == "release":
              ReleaseList.append(MsgObj)
            elif Form["a%d" % Count].value == "delete":
              DeleteList.append(MsgObj)
            elif Form["a%d" % Count].value == "whitelist":
              WhiteList.append(MsgObj)
              ReleaseList.append(MsgObj)
            elif Form["a%d" % Count].value == "blacklist":
              BlackList.append(MsgObj)
              DeleteList.append(MsgObj)
            elif Form["a%d" % Count].value == "report":
              OtherAction = "Report"
              OtherList.append(MsgObj)
            elif Form["a%d" % Count].value == "other":
              if Form["Action"].value == "Release":
                ReleaseList.append(MsgObj)
              elif Form["Action"].value == "Delete":
                DeleteList.append(MsgObj)
              elif Form["Action"].value == "Whitelist":
                WhiteList.append(MsgObj)
                ReleaseList.append(MsgObj)
              elif Form["Action"].value == "Blacklist":
                BlackList.append(MsgObj)
                DeleteList.append(MsgObj)  
              elif Form["Action"].value == "Read":
                ReadList.append(MsgObj)
              else:
                OtherList.append(MsgObj)
                OtherAction = Form["Action"].value
          except (IOError, Errors.MessageError): pass
        # Check for checkboxes (c0 through c%(PagerSize)d)
        elif Form.has_key("c%d" % Count ):
          # Check to make sure they're not trying to access anything other than
          # email
          if not GoodFN.search(Form["m%d" % Count].value):
            CgiUtil.TermError("<tt>%s</tt> is not a valid message ID." %
              Form["m%d" % Count].value, "Program error / corrupted link.",
              "process pending e-mail", "",
              "Recheck link or contact TMDA programmers.")

          try:
            MsgObj = Pending.Message(Form["m%d" % Count].value)
            if Form.has_key("ReleaseButton"):
              ReleaseList.append( MsgObj )
            elif Form.has_key("DeleteButton"):
              DeleteList.append( MsgObj )
            elif Form.has_key("BlacklistButton"):
              BlackList.append( MsgObj )
              DeleteList.append( MsgObj )
            elif Form.has_key("WhitelistButton"):
              WhiteList.append( MsgObj )
              ReleaseList.append( MsgObj )
            elif Form.has_key("ReportButton"):
              OtherAction = "Report"
              OtherList.append( MsgObj )
            elif Form.has_key("ExecuteButton"):
              OtherAction = Form["Action"].value
              if OtherAction == "Release":
                ReleaseList.append( MsgObj )
              elif OtherAction == "Delete":
                DeleteList.append( MsgObj )
              elif OtherAction == "Whitelist":
                WhiteList.append( MsgObj )
                ReleaseList.append( MsgObj )
              elif OtherAction == "Blacklist":
                BlackList.append( MsgObj )
                DeleteList.append( MsgObj )
              elif OtherAction == "Read":
                ReadList.append( MsgObj )
              else: 
                OtherList.append( MsgObj )
          except IOError: pass
      # Process the messages found:
      # Apply "other" action... May be Report or a custom filter
      for MsgObj in OtherList:
        if OtherAction == "Report":
          CgiUtil.ReportToSpamCop(MsgObj)
          DeleteList.append(MsgObj)
        # TODO: Check if OtherAction is a custom filter
        #       If so, run it on the message and check the return value
        #       and add the MsgObj to the appropriate action list based on the
        #       filter output.
      for MsgObj in WhiteList:
        # Whitelist (and release) each message
        MsgObj.whitelist()
      for MsgObj in ReleaseList:
        # Release each message
        PVars["InProcess"][MsgObj.msgid] = 1
        MsgObj.release()
      for MsgObj in BlackList:
        # Blacklist (and delete) each message
        MsgObj.blacklist()
      for MsgObj in DeleteList:
        # Delete each message
        MsgObj.delete()

  # Locate messages in pending dir
  Queue = Pending.Queue(descending = 1, cache = 1)
  try:
    Queue.initQueue()
    Queue._loadCache()
    Msgs = Queue.listPendingIds()
  except (Errors.QueueError, TypeError):
    Msgs = []

  # Search the Pending List:
  #
  #  If the from has the keys searchPattern and search
  #  we can search.
  #
  #  - searchPattern: a basic RE pattern which contains exactly one "%s" 
  #    where the user's search string goes.
  #  - search: The user's search string for incorporation into the searchPattern
  #
  # For an example, check out the source for the Pending List in the theme 
  # 'Blue'
  #
  Searching = 0
  if Form.has_key("searchPattern") and Form.has_key("search"):
    Searching = 1
    # By default, set no flags.
    flags = 0

    # Check what sort of search - a full body search or just a header search
    if( re.search( '%s', Form['searchPattern'].value ) ):
      searchScope = 'fullMessage'
      expression = Form['searchPattern'].value % Form['search'].value
      # Do a multiline search through the entire message, matching a newline
      # with '.'
      flags = re.MULTILINE | re.DOTALL
    elif( re.match( '^_header:', Form['searchPattern'].value ) ):
      ( searchScope, headerList ) = Form['searchPattern'].value.split(':')
      headerList = headerList.split(',')
      expression = Form['search'].value
    elif( Form['searchPattern'].value == "_header" and \
          Form.has_key("searchHeaderList" ) ):
      searchScope = Form['searchPattern'].value
      headerList = Form['searchHeaderList'].value.split(',')
      expression = Form['search'].value

    # Assume case-insensitive unless the form has 'searchCaseSensitive'
    if not Form.has_key("searchCaseSensitive"):
      flags = flags | re.I

    exp = re.compile(expression, flags)
    matchingMsgs = []
    for Msg in Msgs:
      try:
        MsgObj = Pending.Message(Msg)
      except (IOError, Errors.MessageError, TypeError), ErrStr:
        continue
      # Slow search - Search the fulltext of the message
      if searchScope == 'fullMessage' and \
         exp.search( MsgObj.show() ) != None:
        matchingMsgs = matchingMsgs + [ Msg ]
      # Faster search - just matches a header
      elif searchScope == '_header':
        for header in headerList:
          if MsgObj.msgobj.has_key( header ) and \
             exp.search( MsgObj.msgobj[ header ] ):
            matchingMsgs = matchingMsgs + [ Msg ]
            break
    Msgs = matchingMsgs
    # TODO: Catch the error which results if no matches are found.

  # Mark messages as read if necessary
  for MsgObj in ReadList:
    # Mark as Read
    Queue._addCache(MsgObj.msgid)
    Queue._saveCache()

  # Any messages no longer "in process"?
  for PMsg in PVars["InProcess"].keys()[:]:
    try:
      Msgs.index(PMsg)
    except ValueError:
      del PVars["InProcess"][PMsg]

  # Load the display template
  T = Template.Template("pending.html")
  T["CharSet"] = "utf-8"
  T["MsgID"]   = ""

  if Searching:
    # TODO: If searching, we must either:
    #       - Save the search results from page to page
    #       - Show all the search results in the one page, disregarding 
    #         pager settings
    T['searchForm']
  else:
    T['clearSearch']

  # Find the message numbers we'll display
  FirstMsg = PVars["Pager"]
  if Form.has_key("subcmd"):
    if Form["subcmd"].value == "first":
      FirstMsg = 0
    elif Form["subcmd"].value == "prev":
      FirstMsg -= int(PVars[("PendingList", "PagerSize")])
    elif Form["subcmd"].value == "next":
      FirstMsg += int(PVars[("PendingList", "PagerSize")])
    elif Form["subcmd"].value == "last":
      FirstMsg = len(Msgs)
    elif Form["subcmd"].value == "allread":
      for Msg in Msgs:
        Queue._addCache(Msg)
        Queue._saveCache()
  if FirstMsg >= len(Msgs):
    FirstMsg = len(Msgs) - \
               (len(Msgs) % int(PVars[("PendingList", "PagerSize")]) )
  if FirstMsg >= len(Msgs):
    FirstMsg -= int(PVars[("PendingList", "PagerSize")])
  if FirstMsg < 0:
    FirstMsg = 0
  if len(Msgs) <= int(PVars[("PendingList", "PagerSize")]):
    FirstMsg = 0
  LastMsg = FirstMsg + int(PVars[("PendingList", "PagerSize")])
  if LastMsg > len(Msgs):
    LastMsg = len(Msgs)
  if len(Msgs):
    T["DispRange"] = "%d-%d of %d" % (FirstMsg + 1, LastMsg, len(Msgs))
    numPages = len(Msgs) / int(PVars[("PendingList", "PagerSize")])
    if len(Msgs) % int(PVars[("PendingList", "PagerSize")]) > 0:
      numPages += 1
    pageNum = ( FirstMsg / int(PVars[("PendingList", "PagerSize")]) ) + 1
    T["PageRange"] = "%d of %d" % ( pageNum, numPages )

    # Grey out the first & prev buttons?
    if FirstMsg == 0:
      T["FirstButton1Active"]
      T["PrevButton1Active"]
      T["FirstButton2Active"]
      T["PrevButton2Active"]
    else:
      T["FirstButton1Inactive"]
      T["PrevButton1Inactive"]
      T["FirstButton2Inactive"]
      T["PrevButton2Inactive"]

    # Grey out the next & last buttons?
    if LastMsg == len(Msgs):
      T["NextButton1Active"]
      T["LastButton1Active"]
      T["NextButton2Active"]
      T["LastButton2Active"]
    else:
      T["NextButton1Inactive"]
      T["LastButton1Inactive"]
      T["NextButton2Inactive"]
      T["LastButton2Inactive"]

  else:
    T["DispRange"] = "0"
    T["PageRange"] = "1 of 1"

  # Update session
  PVars["Pager"] = FirstMsg
  PVars.Save()

  NumCols = int(T["NumCols"])
  NumBlankCols = int(T["NumBlankCols"])

  # Grab the radiobuttons if they exist
  RlRadio = T["RlRadio"]
  DlRadio = T["DlRadio"]
  WhRadio = T["WhRadio"]
  BlRadio = T["BlRadio"]
  ScRadio = T["SCRadio"]

  # TODO: Programatically check a setting to see which are allowed,
  #       and which should be shown.
  # For now, allow everything
  RlAllowed = 1
  DlAllowed = 1
  WhAllowed = 1 and Defaults.PENDING_WHITELIST_APPEND
  BlAllowed = 1 and Defaults.PENDING_BLACKLIST_APPEND
  ScAllowed = 1 and PVars[("General", "SpamCopAddr")]
  FltAllowed = 1
  RlShow    = RlAllowed and 1
  DlShow    = DlAllowed and (PVars[("PendingList", "ShowDelete")] == "Yes")
  WhShow    = WhAllowed and 1
  BlShow    = BlAllowed and (PVars[("PendingList", "ShowBlack")] == "Yes")
  ScShow    = ScAllowed and 1
 
  if not RlAllowed:
    T["RlAction"]
  if not RlShow:
    T["RlIcon"]
    NumCols -= 1
    NumBlankCols -= 1
  if not DlAllowed:
    T["DlAction"]
  if not DlShow:
    T["DlIcon"]
    NumCols -= 1
    NumBlankCols -= 1
  if not WhAllowed:
    T["WhAction"]
  if not WhShow:  
    T["WhIcon"]
    NumCols -= 1
    NumBlankCols -= 1
  if not BlAllowed:
    T["BlAction"]
  if not BlShow:
    T["BlIcon"]
    NumCols -= 1
    NumBlankCols -= 1
  if not ScAllowed:
    T["ScAction"]
  if not ScShow:
    T["SCIcon"]
    NumCols -= 1
    NumBlankCols -= 1
    
  if FltAllowed:
    T["FilterOptions"] = CgiUtil.getFilterOptions() 
  else:
    T["FilterOptions"] = ""

  T["NumCols"] = NumCols
  T["NumBlankCols"] = NumBlankCols

  # Javascript confirmation?
  if PVars[("General", "UseJSConfirm")] == "Yes":
    T["OnSubmit"] = 'onSubmit="return TestConfirm()"'
  else:
    T["OnSubmit"] = ""
  T["PagerSize"] = PVars[("PendingList", "PagerSize")]

  ReadArray = []

  # Parse out embedded variables from template
  Row          = T["Row"]
  InProcessRow = T["InProcessRow"]
  InProcess    = T["InProcess"]
  try:
    EvenRowColor = T["EvenRowColor"]
    OddRowColor  = T["OddRowColor"]
  except:
    EvenRowColor = None
    OddRowColor  = None
  try:
    RowBgColor   = T["RowBgColor"]
  except:
    RowBgColor   = None  
  if len(Msgs):
    # Add rows for messages if there are any
    Count = 0
    #InProcMsg = ""
    inProcessLine = 0
    for Msg in Msgs[FirstMsg:LastMsg]:
      T["MsgID"] = Msg
      if Count % 2 == 0 and OddRowColor is not None:
        T["RowBgColor"] = OddRowColor
      elif EvenRowColor is not None:
        T["RowBgColor"] = EvenRowColor

      # Print a single message record inside list loop
      try:
        MsgObj = Pending.Message(Msg)
      except (IOError, Errors.MessageError, \
              email.Errors.MessageError), ErrStr:
        continue

      # Message size
      T["Size"] = CgiUtil.Size(MsgObj)

      # Find preferred date
      DateFormat = PVars[("PendingList", "DateFormat")]
      MsgTime = int(MsgObj.msgid.split('.')[0])
      if DateFormat == "DaysAgo":
        # Special Case!  "n days ago"
        Today = (int(time.time()) / 86400)
        MsgDay = (MsgTime / 86400)
        DaysAgo = Today - MsgDay
        if DaysAgo == 0:
          Date = "Today"
        elif DaysAgo == 1:
          Date = "Yesterday"
        else:
          Date = "%d days ago" % DaysAgo
      else:
        # General case - strftime format
        Date = time.strftime \
        (
          PVars[("PendingList", "DateFormat")],
          time.localtime(MsgTime)
        )
      T["Date"] = ZeroSearch.sub(ZeroSub, Date)

      # Character set
      CharSet = CgiUtil.FindCharSet(MsgObj)

      # Subject:
      if not MsgObj.msgobj["subject"]:
        Subject = "None"
      else:
        # Decode internationalazed headers
        value = ""
        for decoded in email.Header.decode_header( MsgObj.msgobj["subject"] ):
          if decoded[1]:
            try:
              value += Unicode.TranslateToUTF8(decoded[1], decoded[0], "strict")
            except UnicodeError:
              value += Unicode.TranslateToUTF8(CharSet, decoded[0], "ignore")
          else:
            value += Unicode.TranslateToUTF8(CharSet, decoded[0], "ignore")
        Subject = value
        if len(Subject) > int(PVars[("PendingList", "CropSubject")]):
          Subject = \
            cgi.escape(Subject[:int(PVars[("PendingList", "CropSubject")])
              - 1]) + "&#8230;"
        else:
          Subject = cgi.escape(Subject)
      T["Subject"] = Subject

      # From:
      if not MsgObj.msgobj["from"]:
        From = ""
      else:
        # Decode internationalazed headers
        value = ""
        for decoded in email.Header.decode_header( MsgObj.msgobj["from"] ):
          if decoded[1]:
            try:
              value += Unicode.TranslateToUTF8(decoded[1], decoded[0], "strict")
            except UnicodeError:
              value += Unicode.TranslateToUTF8(CharSet, decoded[0], "ignore")
          else:
            value += Unicode.TranslateToUTF8(CharSet, decoded[0], "ignore")
        From = value
        Temp = Address.search(From)
        if Temp:
          if PVars[("PendingList", "ShowAddr")] == "Name":
            From = Temp.group(1)
          if PVars[("PendingList", "ShowAddr")] == "Address":
            From = Temp.group(2)
      if len(From) > int(PVars[("PendingList", "CropSender")]):
        From = cgi.escape(From[:int(PVars[("PendingList", "CropSender")]) -
          1]) + "&#8230;"
      else:
        From = cgi.escape(From)
      T["Sender"] = From

      # To:
      if not MsgObj.msgobj["to"]:
        To = ""
      else:
        To = MsgObj.msgobj["to"]
        Temp = Address.search(To)
        if Temp:
          if PVars[("PendingList", "ShowAddr")] == "Name":
            To = Temp.group(1)
          if PVars[("PendingList", "ShowAddr")] == "Address":
            To = Temp.group(2)
      if len(To) > int(PVars[("PendingList", "CropDest")]):
        To = cgi.escape(To[:int(PVars[("PendingList", "CropDest")]) -
          1]) + "&#8230;"
      else:
        To = cgi.escape(To)
      T["To"] = To

      if PVars["InProcess"].has_key(Msg):
        # Message is "in process"  
        if not inProcessLine:
          InProcess.Clear()
          InProcess.Add()
          inProcessLine = 1
        InProcessRow.Add()
      else:
        # Message is not "in process"
        T["RadioName"] = "a%d" % Count
        T["CheckName"] = "c%d" % Count
        T["MsgName"]   = "m%d" % Count
        T["MsgNum"]    = Count
        T["MsgID"]     = Msg

        # Read this one yet?
        if Msg in Queue.msgcache:
          T["MsgClass"] = "OldMsg"
          ReadArray.append(1)
        else:
          T["MsgClass"] = "NewMsg"
          ReadArray.append(0)

        if RlShow and RlRadio:
          RlRadio.Clear()
          RlRadio.Add()
        if DlShow and DlRadio:
          DlRadio.Clear()
          DlRadio.Add()
        if WhShow and WhRadio:
          WhRadio.Clear()
          WhRadio.Add()
        if BlShow and BlRadio:
          BlRadio.Clear()
          BlRadio.Add()
        if ScShow and ScRadio:
          ScRadio.Clear()
          ScRadio.Add()

        Row.Add()
        Count = Count + 1
    
    ReadArrayText = "ReadArray = new Array("
    for SubCount in range( 0, Count ):
      if ReadArray[SubCount]:
        ReadArrayText += "true"
      else:
        ReadArrayText += "false"
      if SubCount == ( Count - 1 ):
        ReadArrayText += ")"
      else:
        ReadArrayText += ", "
    T["ReadArray"] = ReadArrayText

    # Disallow searching if defaults.ini prohibits
    if not Searching and PVars[("NoOverride", "MaySearchPendList")][0].lower() == "n":
      T['searchForm']

  # No messages to display
  else:
    T["ReadArray"] = ""
    T["FirstButton1Active"]
    T["PrevButton1Active"]
    T["FirstButton2Active"]
    T["PrevButton2Active"]
    T["NextButton1Active"]
    T["LastButton1Active"]
    T["NextButton2Active"]
    T["LastButton2Active"]
    if Searching:
      T["Row"] = '<tr><td colspan="%s" align="center" class="InProcess"><i>No messages match the search criteria</i></td></tr>' % NumCols
    else: 
      T["Row"] = '<tr><td colspan="%s" align="center" class="InProcess"><i>No messages in your pending queue</i></td></tr>' % NumCols
      T['searchForm']

  print T
