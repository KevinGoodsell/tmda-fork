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

"Test dynamic addresses for tmda-cgi."

import os
import time
import Template
from TMDA import Address
from TMDA import Defaults

# Constants
DateFormat = "%a, %d %b %Y %H:%M:%S UTC"

def Show():
  "Test dynamic addresses."

  # Load the display template
  T = Template.Template("test_addr.html")
  Sender  = T["Sender"]
  Results = T["ShowResults"]

  # Not sure yet which form we'll use, so put something in each field.
  if PVars.has_key(("TestAddr", "To")):
    T["To"] = PVars[("TestAddr", "To")]
  else:
    T["To"] = ""
  if PVars.has_key(("TestAddr", "From")):
    T["From"] = PVars[("TestAddr", "From")]
  else:
    T["From"] = ""

  # Do we have an address to test?
  if Form.has_key("subcmd"):

    # Get and save form data
    if Form.has_key("from"):
      From = T["From"] = PVars[("TestAddr", "From")] = Form["from"].value
    else:
      if PVars.has_key(("TestAddr", "From")):
        del PVars[("TestAddr", "From")]
      From = T["From"] = ""
    if Form.has_key("to"):
      T["To"] = PVars[("TestAddr", "To")] = Form["to"].value

      # Remove the instructions
      T["Instructions"]

      # Test the address
      try:
        Addr = Address.Factory(PVars[("TestAddr", "To")])
        Addr.verify(From)
        T["Results"] = "Valid."
        try:
          T["Results"] = "Valid.<br>Expires: %s" % \
            time.strftime(DateFormat, time.localtime(int(Addr.timestamp())))
        except AttributeError:
          pass
      except Address.AddressError, Msg:
        T["Results"] = Msg
        try:
          T["Results"] = "Expired or invalid<br>Expiration: %s" % \
            time.strftime(DateFormat, time.localtime(int(Addr.timestamp())))
        except AttributeError:
          pass

      # Add results in their place
      if PVars.has_key(("TestAddr", "From")): Sender.Add()
      Results.Add()

    else: # (no "to" field)
      if PVars.has_key(("TestAddr", "To")):
        del PVars[("TestAddr", "To")]
      T["To"] = ""

  # Display template
  print T
