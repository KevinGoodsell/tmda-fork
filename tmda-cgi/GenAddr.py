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

"Generate dynamic addresses for tmda-cgi."

import os
import Template
import CgiUtil
from TMDA import Address
from TMDA import Defaults

def Show():
  "Generate dynamic addresses."

  # Load the display template
  T = Template.Template("gen_addr.html")

  # Not sure yet which form we'll use, so put something in each field.
  T["Keyword"]     = PVars[("GenAddr", "Keyword")]
  T["KeywordAddr"] = ""
  T["ExpAmt"]      = int(PVars[("GenAddr", "ExpireNum")])
  T["mSel"]        = ""
  T["hSel"]        = ""
  T["dSel"]        = ""
  T["wSel"]        = ""
  T["MSel"]        = ""
  T["YSel"]        = ""
  T["DatedAddr"]   = ""
  T["Sender"]      = PVars[("GenAddr", "Sender")]
  T["SenderAddr"]  = ""
  
  #
  # What shall we create?
  #
  T["defaultAddress"] = Address.Factory().create(None).address

  # Default is "dated"
  Tag = Defaults.TAGS_DATED[0].lower()
  if Form.has_key("dated_addr"):
    Base = Form["dated_addr"].value
  else:
    Base = None
  DestField = "DatedAddr"

  if Form.has_key("subcmd"):
    if Form["subcmd"].value == "sender":

      # Make a "sender" address
      Tag = Defaults.TAGS_SENDER[0].lower()
      if Form.has_key("sender_addr"):
        Base = Form["sender_addr"].value
      else:
        Base = None
      DestField = "SenderAddr"
      if Form.has_key("sender"):
        Option = T["Sender"] = PVars[("GenAddr", "Sender")] = \
          PVars[("TestAddr", "From")] = Form["sender"].value
      else:
        if PVars.has_key(("GenAddr", "Sender")):
          del PVars[("GenAddr", "Sender")]
        if PVars.has_key(("TestAddr", "From")):
          del PVars[("TestAddr", "From")]
        T["Sender"] = ""
        DestField = ""
      PVars.Save()

    elif Form["subcmd"].value == "keyword":

      # Make a "keyword" address
      Tag = Defaults.TAGS_KEYWORD[0].lower()
      if Form.has_key("keyword_addr"):
        Base = Form["keyword_addr"].value
      else:
        Base = None
      DestField = "KeywordAddr"
      if Form.has_key("keyword"):
        Option = T["Keyword"] = PVars[("GenAddr", "Keyword")] = \
          Form["keyword"].value
      else:
        if PVars.has_key(("GenAddr", "Keyword")):
          del PVars[("GenAddr", "Keyword")]
        T["Keyword"] = ""
      if PVars.has_key(("TestAddr", "From")):
        del PVars[("TestAddr", "From")]
      PVars.Save()
    
    else:
    
      # Make a "dated" address
      PVars[("GenAddr", "ExpireUnit")] = Form["exp_units"].value
      if Form.has_key("exp_amt"):
        T["ExpAmt"] = PVars[("GenAddr", "ExpireNum")] = \
          int(Form["exp_amt"].value)
        Option = "%d%s" % (int(PVars[("GenAddr", "ExpireNum")]),
          PVars[("GenAddr", "ExpireUnit")])
      else:
        if PVars.has_key(("GenAddr", "ExpireNum")):
          del PVars[("GenAddr", "ExpireNum")]
      if PVars.has_key(("TestAddr", "From")):
        del PVars[("TestAddr", "From")]
      PVars.Save()

  # Default to dated
  else:
    if PVars.has_key(("TestAddr", "From")):
      del PVars[("TestAddr", "From")]
    Option = "%d%s" % (int(PVars[("GenAddr", "ExpireNum")]),
      PVars[("GenAddr", "ExpireUnit")])

  # Show correct units
  T["%sSel" % PVars[("GenAddr", "ExpireUnit")]] = " selected"

  # Strip the Base if it is already a tagged address.
  if Base is not None:
    try:
      at = Base.rindex('@')
      local = Base[:at].lower()
      domain = Base[at+1:].lower()
    except ValueError:
      CgiUtil.TermError("Value Error", 
        "'%s' is not a valid email address" % Base,
        "generate address", "",
        "Try again with a valid email address in the <i>Use Address</i> blank."
        )
    addr = Address.Factory(Base)
    addrTag = addr.tag()
    if addrTag != "":
      tagindex = local.rindex( addrTag )
      Base = local[:tagindex - 1] + "@" + domain

  # Create the address
  try:
    T[DestField] = PVars[("TestAddr", "To")] = \
      Address.Factory(tag = Tag).create(Base, Option).address
    PVars.Save()
  except (TypeError, UnboundLocalError):
    pass

  # Display template
  print T
