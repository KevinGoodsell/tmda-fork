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

"Unicode utilities for tmda-cgi."

import codecs
import re

import Template

# Handy values
AltChar  = re.compile("[\x80-\xFF]")
UTF8     = codecs.lookup("utf-8")[0]

def Xlate(Chr):
  if ord(Chr) >= 160: return unichr(ord(Chr))
  if Chr == "€": return u"\u20AC"
  if Chr == "‚": return u"\u201A"
  if Chr == "ƒ": return u"\u2061"
  if Chr == "„": return u"\u201E"
  if Chr == "…": return u"\u2026"
  if Chr == "†": return u"\u2020"
  if Chr == "‡": return u"\u2021"
  if Chr == "‰": return u"\u2030"
  if Chr == "‹": return u"\u2039"
  if Chr == "‘": return u"\u2018"
  if Chr == "’": return u"\u2019"
  if Chr == "“": return u"\u201C"
  if Chr == "”": return u"\u201D"
  if Chr == "•": return u"\u2022"
  if Chr == "–": return u"\u2014"
  if Chr == "—": return u"\u2015"
  if Chr == "™": return u"\u2122"
  return u"\u007F"

def Iso8859(Str):
  RetVal = u""
  while 1:
    Match = AltChar.search(Str)
    if Match:
      RetVal += Str[:Match.start()] + Xlate(Match.group(0))
      Str = Str[Match.end():]
    else:
      break
  RetVal += Str
  return (RetVal,)

def TranslateToUTF8(CharSet, Str, Errors):
  "Represent a string in UTF-8."
  import email.Charset

  if not CharSet: CharSet = "iso-8859-1"
  CS = email.Charset.Charset(CharSet)
  CharSet = CS.input_charset

  # Find appropriate decoder
  if CharSet in ("iso-8859-1", "us-ascii"):
    Decoder = Iso8859
  else:
    try:
      Decoder = codecs.lookup(CharSet)[1]
    except LookupError:
      try:
        # Is it GB2312?
        if CharSet == "gb2312":
          import chinese.gb2312
          Lib = chinese.gb2312
        # Is it GBK?
        elif CharSet == "gbk":
          import chinese.gbk
          Lib = chinese.gbk
        # Is it Big5?
        elif CharSet == "big5":
          import chinese.big5
          Lib = chinese.big5
        # Is it iso-2022-jp?
        elif CharSet == "iso-2022-jp":
          import japanese.iso_2022_jp_ext
          Lib = japanese.iso_2022_jp_ext
        # Don't recognize it.  Was it our fallback?
        elif CharSet == PVars[("General", "CSEncoding")]:
          # It was our fallback!  Give up now!
          return Str
        # Mark it and use the fallback
        else:
          return "(%s) %s" % (CharSet,
            TranslateToUTF8(PVars[("General", "CSEncoding")], Str, Errors))
        Decoder = Lib.Codec().decode
      except ImportError:
        # We know what it was, but we don't have the library installed.
        return "(%s) %s" % (CharSet, Str)

  # Decode string to Unicode
  try:
    Uni = Decoder(Str, errors = Errors)[0]
  except:
    Uni = Decoder(Str)[0]

  # Encode for UTF-8
  return UTF8(Uni)[0]
