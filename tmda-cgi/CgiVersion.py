# -*- python -*-
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
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

"""Various versioning information."""

from TMDA import Version

# tmda-cgi version
tmda_cgi = "0.13"

# tmda-cgi version codename
Codename = "Aluminum"

# TMDA version required
TMDAReqVer = "0.81"

# Python version
Python = Version.PYTHON

# Platform identifier
Platform = Version.PLATFORM

# Summary of all the version identifiers
# e.g, tmda-cgi/0.02 "Helium" (Python/2.2.2 on linux-i686)
All = 'tmda-cgi/%s "%s" (Python/%s on %s)' % \
  (tmda_cgi, Codename, Python, Platform)

def Test():
  "Validate TMDAReqVer."
  if Version.TMDA < TMDAReqVer:
    raise ImportError, \
      "tmda-cgi/%s requires TMDA/%s or later.  TMDA/%s found." % \
      (tmda_cgi, TMDAReqVer, Version.TMDA)
