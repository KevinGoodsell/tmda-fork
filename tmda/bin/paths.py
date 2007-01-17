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

"""Fixup sys.path."""

import os
import sys

progpath = os.path.abspath(sys.argv[0])

# Handle symbolic links.
if os.path.islink(progpath):
    progdir = os.path.dirname(progpath)
    linkpath = os.readlink(progpath)
    if os.path.isabs(linkpath):
        progpath = linkpath
    else:
        progpath = os.path.normpath(progdir + '/' + linkpath)

# Hack the path to include the parent directory ('../')
prefix = os.path.split(os.path.dirname(progpath))[0]
sys.path.insert(0, prefix)

# We also need the TMDA/pythonlib directory on the path to pick up any
# overrides of standard modules and packages.  Note that these must go
# at the very front of the path for this reason.
sys.path.insert(0, os.path.join(prefix, 'TMDA', 'pythonlib'))
