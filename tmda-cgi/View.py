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

"View e-mail page for tmda-cgi."

import cgi
import email
import os
import re
import CgiUtil
from TMDA import Defaults
from TMDA import Pending
from TMDA import Util

# Pre-calc the regular expressions
TextType    = re.compile("^text/")
MessageType = re.compile("^(message|multipart)/")
ImageType1  = re.compile("\.(GIF|JPG)$", re.I)
ImageType2  = re.compile("^image/")
MovieType1  = re.compile("\.(MOV|AVI|SWF)$", re.I)
MovieType2  = re.compile("^(video/|application/x-shockwave)")
PythonType1 = re.compile("\.(PY|PYC|PYO)$", re.I)
SoundType1  = re.compile("\.(AU|SND|MP3|WAV)$", re.I)
SoundType2  = re.compile("^audio/")
TextType1   = re.compile("\.(TXT)$", re.I)
ZipType1    = re.compile("\.(TGZ|ZIP|BZ|BZ2)$", re.I)
ZipType2    = re.compile("^application/zip")

def Attachment(Part):
  "Generates some HTML to display an icon representing the attachment."
  Filename = Part.get_filename("")
  Icon = "exe"
  if ImageType1.search(Filename): Icon = "image"
  elif MovieType1.search(Filename): Icon = "movie"
  elif PythonType1.search(Filename): Icon = "python"
  elif SoundType1.search(Filename): Icon = "sound"
  elif TextType1.search(Filename): Icon = "text"
  elif ZipType1.search(Filename): Icon = "zip"
  elif ImageType2.search(Part.get_type("text/plain")): Icon = "image"
  elif MovieType2.search(Part.get_type("text/plain")): Icon = "movie"
  elif SoundType2.search(Part.get_type("text/plain")): Icon = "sound"
  elif ZipType2.search(Part.get_type("text/plain")): Icon = "zip"
  return """<td>
  <img src=%s.gif width=32 height=32><br>
  %s<br>
  (%s)
</td>
<td width="10">
</td>""" % (CgiUtil.DispDir + Icon, Filename, CgiUtil.Size(Part))

def Show():
  "Show an e-mail in HTML."

  # Check to make sure they're not trying to access anything other than email
  if not re.compile("^\d+\.\d+\.msg$").search(PVars["MsgID"]):
    CgiUtil.TermError("<tt>%s</tt> is not a valid message ID." % PVars["MsgID"],
      "Program error / corrupted link.", "retrieve pending e-mail", "",
      "Recheck link or contact TMDA programmers.")

  # Fetch the queue
  Queue = Pending.Queue(descending = (PVars["SortDir"] == "desc"), cache = 1)
  Queue.initQueue()
  Queue._loadCache()
  
  # Any subcommands?
  if Form.has_key("subcmd"):
    # Locate messages in pending dir
    Msgs = Queue.listPendingIds()
    try:
      MsgIdx = Msgs.index(PVars["MsgID"])
    except ValueError: # Oops.  Perhaps they released the message?  Get the list!
      print "Location: %s?cmd=pending&SID=%s\n" % \
        (os.environ["SCRIPT_NAME"], PVars.SID)
      return
    
    # first/prev/next/last subcommands
    if Form["subcmd"].value == "first":
      PVars["MsgID"] = Msgs[0]
      PVars["Pager"] = 0
    elif Form["subcmd"].value == "prev":
      if MsgIdx > 0:
        PVars["MsgID"] = Msgs[MsgIdx - 1]
        PVars["Pager"] -= 1
    elif Form["subcmd"].value == "next":
      if MsgIdx < (len(Msgs) - 1):
        PVars["MsgID"] = Msgs[MsgIdx + 1]
        PVars["Pager"] += 1
    elif Form["subcmd"].value == "last":
      PVars["MsgID"] = Msgs[-1]
      PVars["Pager"] = len(Msgs)
    
    else:
      # Read in e-mail
      try:
        MsgObj = Pending.Message(PVars["MsgID"])
  
        if Form["subcmd"].value == "delete":
          MsgObj.delete()
        elif Form["subcmd"].value == "release":
          MsgObj.release()
          PVars["InProcess"][PVars["MsgID"]] = 1
        elif Form["subcmd"].value == "white":
          MsgObj.whitelist()
          MsgObj.release()
          PVars["InProcess"][PVars["MsgID"]] = 1
        elif Form["subcmd"].value == "black":
          MsgObj.blacklist()
          MsgObj.delete()
        del Msgs[MsgIdx]
      except IOError: pass
      
      # So which message are we on now?
      if len(Msgs) == 0: # Oops! None left!
        print "Location: %s?cmd=pending&SID=%s\n" % \
          (os.environ["SCRIPT_NAME"], PVars.SID)
        PVars.Save()
        return
      if MsgIdx >= len(Msgs): PVars["MsgID"] = Msgs[-1]
      else:                   PVars["MsgID"] = Msgs[MsgIdx]

    # Save session
    PVars.Save()

  # Use Javascript confirmation?
  if Defaults.CGI_USE_JS_CONFIRM:
    DeleteLink = "javascript:ConfirmDelete()"
    BlackLink  = "javascript:ConfirmBlacklist()"
  else:
    DeleteLink = "%s?cmd=view&subcmd=delete&SID=%s" % \
      (os.environ["SCRIPT_NAME"], PVars.SID)
    BlackLink  = "%s?cmd=view&subcmd=black&SID=%s" % \
      (os.environ["SCRIPT_NAME"], PVars.SID)
  
  # Read in e-mail
  MsgObj = Pending.Message(PVars["MsgID"])
  Queue._addCache(PVars["MsgID"])
  Queue._saveCache()
  
  if PVars["Headers"] == "all":
    # Generate all headers
    MsgHTML = """<a href="%s?cmd=view&headers=short&SID=%s"><img 
  src="%sshorthead.gif" width="100" height="65" align="right" border="0" 
  alt="Show Short Headers"></a><pre>""" % (os.environ["SCRIPT_NAME"],
      PVars.SID, CgiUtil.DispDir)
    for Line in CgiUtil.Escape(MsgObj.show()).split("\n"):
      if Line == "": break
      MsgHTML += Line + "\n"
    MsgHTML += "</pre>"
  else:
    # Generate short headers
    MsgHTML = """<a href="%s?cmd=view&headers=all&SID=%s"><img 
  src="%sallhead.gif" width="100" height="65" align="right" border="0" 
  alt="Show All Headers"></a>
<table class="Headers" border="0" cellspacing="0" cellpadding="0">
""" % (os.environ["SCRIPT_NAME"], PVars.SID, CgiUtil.DispDir)
    for Header in Defaults.SUMMARY_HEADERS:
      MsgHTML += """  <tr>
    <th>%s:</th>
    <td width="5"></td>
    <td>%s</td>
  </tr>
""" % (Header.capitalize(), CgiUtil.Escape(MsgObj.msgobj[Header]))
    MsgHTML += "</table><p>"
  
  # Go through each part and generate HTML
  TextParts = 0
  Attachments = ""
  for Part in MsgObj.msgobj.walk():
    Type = Part.get_type("text/plain")
    # Display the easily display-able parts
    if TextType.search(Type):
      TextParts += 1
      if TextParts > 1: MsgHTML += "<hr class=PartDiv>"
      if Type == "text/plain":
        try:
          MsgHTML += "<span class=EmailText>%s</span>" % \
            CgiUtil.Escape(Part.get_payload(decode=1).strip()).replace("\n", "&nbsp;<br>")
        except AttributeError:
          pass
      else:
        MsgHTML += Part.get_payload(decode=1)
    # Don't show anything if the part contains other parts
    # (those parts will be recursed seperately)
    elif not MessageType.search(Type):
      # Create an icon to show other attachments
      Attachments += Attachment(Part)
  # Show any attachments at the bottom of the email
  if Attachments != "":
    TextParts += 1
    if TextParts > 1: MsgHTML += "<hr class=PartDiv>"
    MsgHTML += """<table class=Attachments>
  <tr>
    %s
  </tr>
</table>
""" % Attachments

  # Any extra icons?
  Columns = 7
  ExtraIcon1 = ""
  ExtraIcon2 = ""
  if Defaults.PENDING_BLACKLIST_APPEND:
    Columns += 1
  if Defaults.PENDING_WHITELIST_APPEND:
    Columns += 1
  ColWidth = "%d%%" % int(100 / Columns)
  if Defaults.PENDING_BLACKLIST_APPEND:
    ExtraIcon1 = """<td width="%s"><a href="%s"><img alt="Blacklist & Delete" 
      src="%sblack.gif" width="38" height="42" border="0"></a></td>
""" % (ColWidth, BlackLink, CgiUtil.DispDir)
  if Defaults.PENDING_WHITELIST_APPEND:
    ExtraIcon2 = """<td width="%s"><a href="%s?cmd=view&subcmd=white&SID=%s"><img 
      alt="Whitelist & Release" src="%swhite.gif" width="40" height="42" 
      border="0"></a></td>
""" % (ColWidth, os.environ["SCRIPT_NAME"], PVars.SID, CgiUtil.DispDir)

  # Precalculate the navigation bar (since we'll use it twice)
  NavBarHTML = """  <tr align="center" class="NavBar">
    <td width="%(width)s"><a href="%(script)s?cmd=view&subcmd=first&SID=%(SID)s"><img alt="First"
      src="%(dir)sfirst.gif" width="24" height="42" border="0"></a></td>
    <td width="%(width)s"><a href="%(script)s?cmd=view&subcmd=prev&SID=%(SID)s"><img alt="Prev"
      src="%(dir)sprev.gif" width="21" height="42" border="0"></a></td>
    <td width="%(width)s"><a href="%(delete)s"><img alt="Delete" src="%(dir)skill.gif" 
      width="30" height="42" border="0"></a></td>%(icon1)s
    <td width="%(width)s"><a href="%(script)s?cmd=list&SID=%(SID)s"><img alt="Entire List"
      src="%(dir)sall.gif" width="45" height="42" border="0"></a></td>
    <td width="%(width)s"><a href="%(script)s?cmd=view&subcmd=release&msgid=%(msgid)s&SID=%(SID)s"><img alt="Release"
      src="%(dir)saccept.gif" width="38" height="42" border="0"></a></td>%(icon2)s
    <td width="%(width)s"><a href="%(script)s?cmd=view&subcmd=next&SID=%(SID)s"><img alt="Next"
      src="%(dir)snext.gif" width="21" height="42" border="0"></a></td>
    <td width="%(width)s"><a href="%(script)s?cmd=view&subcmd=last&SID=%(SID)s"><img alt="Last"
      src="%(dir)slast.gif" width="24" height="42" border="0"></a></td>
  </tr>""" % {"width": ColWidth, "script": os.environ["SCRIPT_NAME"],
    "SID": PVars.SID, "delete": DeleteLink, "icon1": ExtraIcon1,
    "msgid": PVars["MsgID"], "icon2": ExtraIcon2, "dir": CgiUtil.DispDir}


  # Display HTML page with email included.
  print """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>View E-mail</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<link href="%sstyles.css" rel="stylesheet" type="text/css">
</head>

<body class="ViewPage">
<table>
%s
  <tr>
    <td colspan="%d" class="Email">
      <hr class=NavDiv>
      %s
      <hr class=NavDiv>
    </td>
  </tr>
%s
</table>""" % (CgiUtil.DispDir, NavBarHTML, Columns, MsgHTML, NavBarHTML)

  # Javascript confirmation for delete and blacklist?
  if Defaults.CGI_USE_JS_CONFIRM:
    print """<script>
function ConfirmDelete()
{
  if (confirm("Permanently delete this pending message?\\nAny confirmation that follows will fail."))
    document.location.href = "%(script)s?cmd=view&subcmd=delete&msgid=%(msgid)s&SID=%(SID)s"
}
function ConfirmBlacklist()
{
  if (confirm("Blacklist sender and permanently delete this pending message?"))
    document.location.href = "%(script)s?cmd=view&subcmd=black&msgid=%(msgid)s&SID=%(SID)s"
}
</script>""" % {"script": os.environ["SCRIPT_NAME"], "msgid": PVars["MsgID"],
    "SID": PVars.SID}

  print """</body>
</html>"""
