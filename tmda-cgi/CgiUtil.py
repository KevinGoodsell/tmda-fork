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
import codecs
import os
import re
import sys
import time

import Template

from TMDA import Errors

# Handy values
DispDir        = os.environ["TMDA_CGI_DISP_DIR"]
ErrTemplate    = "error2.html"
QuotedString   = re.compile(r"^(['\"])(.*?)\1\s*", re.S)
UnquotedString = re.compile(r"^(\S+)\s*")
HomeDirSearch  = re.compile("^~/")
HTMLTagSearch  = re.compile("</?([^\s>]*).*?>", re.S)

# CGI exception classes
class NotInstalled(Errors.TMDAError):
  "TMDA won't run because the user has not installed it."
  pass

class JustLoggedIn(Errors.TMDAError):
  "Not really an error, but used to trigger a setting of initial variables."
  pass

def Size(MsgObj = None, MsgSize = 0):
  if MsgObj:
    MsgSize = os.stat(MsgObj.msgfile)[6]
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
  try:
    T = Template.Template(ErrTemplate)
  except IOError:
    T = Template.Template(SubTemplate = ["""Error:<br>%(ErrorName)s<p>
Cause:<br>%(Cause)s<p>
Additional:<br>%(Additional)s<p>
Recommend:<br>%(Recommendation)s"""])
  T["ErrorName"]  = Err
  T["Cause"]      = Cause
  T["Additional"] = """Running in %s mode.<br>
Attempted to %s with euid %d, egid %d.<br>
%s""" % (os.environ["TMDA_CGI_MODE"], Failed, os.geteuid(), os.getegid(), Other)
  T["Recommendation"] = Recommend
  print T
  sys.exit(0)

def ParseString(Str, User):
  "Parse a string (possibly with quoted arguments) into a list."
  RetVal = []
  while 1:
    Match = QuotedString.search(Str)
    if Match:
      Arg = Match.group(2)
    else:
      Match = UnquotedString.search(Str)
      if Match:
        Arg = Match.group(1)
    if Match:
      if Arg == "~":
        Arg = User
      RetVal.append(Arg)
      Str = Str[Match.end():]
    else:
      break
  return RetVal

def ExpandUser(Path):
  return HomeDirSearch.sub(os.environ["HOME"] + "/", Path)

def Sterilize(Str, Allow, Remove):
  """Remove all offensive HTML from a given string.

Allow is a list of tags (b, i, etc.) which are allowed and may remain.
Remove is a list of tags which should not only be removed, but all text within
the open and close tag should be removed as well."""
  RetVal = ""
  while 1:
    Match = HTMLTagSearch.search(Str)
    if Match:
      RetVal += Str[:Match.start()]
      Tag = Match.group(1).lower()
      if Tag in Allow:
        RetVal += Match.group(0)
        Str = Str[Match.end():]
      elif Tag in Remove:
        Match = re.search("</%s\s*>" % Tag, Str, re.I)
        if Match:
          Str = Str[Match.end():]
        else:
          return RetVal
      else:
        Str = Str[Match.end():]
    else:
      return RetVal + Str

def ReportToSpamCop(MsgObj):
  "Report a given message to SpamCop."

  if PVars[("NoOverride", "Sendmail")]:
    Sendmail = "-s %s " % PVars[("NoOverride", "Sendmail")]
  else:
    Sendmail = ""
  if PVars[("NoOverride", "SpamCopFilter")]:
    Filter = "%s | " % PVars[("NoOverride", "SpamCopFilter")]
  else:
    Filter = ""
  Command = "%s%s reporter.py %s%s" % (Filter, sys.executable, Sendmail,
    PVars[("General", "SpamCopAddr")])
  P = os.popen(Command, "w")
  P.write(MsgObj.msgobj.as_string(1))
  P.close()

def FindCharSet(MsgObj):
  "Find the character set in an e-mail."
  RetVal = None
  for Part in MsgObj.msgobj.walk():
    CS = Part.get_content_charset()
    if CS: RetVal = CS.split()[0]
  return RetVal

def getFilterOptions():
  "Returns all available custom filters in an HTML <option> list"
  # TODO
  # When there are filters, show them as:
  #
  # "<option value=\"F%d\">%s" % (FilterIndex, FilterName)
  #
  # Where "i" is the index of that filter.
  #

  # For now, show nothing.
  return ""

def TestTextFilePath(Path):
  "Tests Path against regular expressions listed in AccessPaths (defaults.ini)"
  Dict = {"Home": os.environ["HOME"]}
  for Var in PVars.ThemeVars.options("AccessPaths"):
    if re.search(PVars.ThemeVars.get("AccessPaths", Var, 1) % Dict, Path):
      return 1
  for Var in PVars.PVars:
    if Var[:12] == "AccessPaths:":
      if re.search(PVars.PVars[Var] % Dict, Path):
        return 1
  return None
