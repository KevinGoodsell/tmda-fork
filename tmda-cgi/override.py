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

# TODO: Perhaps a check should be put in for the various authentication schemes
# that the arguments are valid.  This is currently done at runtime within
# "Authenticate.py", but it may be better to check at least some of the
# values at compile-time anyway.

"""Override a user's current setting

Usage:  %(Program)s <SettingsFile> <Section:Setting> <Value>

For example:

%(Program)s tmda-cgi.ini NoOverride:MayEditTemplates Yes

Case *IS* signifigant.
"""

import os
import pickle
import sys

Program = sys.argv[0]

if len(sys.argv) != 4:
  # Show usage information
  print __doc__ % globals()
  sys.exit()

Filename, Setting, Value = sys.argv[1:]

# Read in file
PVars = {}
try:
  F = open(Filename)
  PVars = pickle.load(F)
  F.close()
except (IOError, EOFError):
  pass

# Make change
PVars[Setting] = Value

# Save out file
F = open(Filename, "w")
pickle.dump(PVars, F)
F.close()
