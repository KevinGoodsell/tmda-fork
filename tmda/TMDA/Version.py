# -*- python -*-
#
# Copyright (C) 2001-2007 Jason R. Mastaler <jason@mastaler.com>
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


import platform


# TMDA version
TMDA = '1.1.12'

# TMDA version codename
CODENAME = 'Macallan'

# Python version
PYTHON = platform.python_version()

# Platform identifier
PLATFORM = platform.platform()

# Summary of all the version identifiers
# e.g, TMDA/1.1.0 "Aberfeldy" (Python/2.3.2 on Darwin-6.8-Power_Macintosh-powerpc-32bit)
ALL = 'TMDA/%s "%s" (Python/%s on %s)' % (TMDA, CODENAME, PYTHON, PLATFORM)
