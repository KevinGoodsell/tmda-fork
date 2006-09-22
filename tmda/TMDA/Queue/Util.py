# -*- python -*-
#
# Copyright (C) 2001,2002,2003,2004,2005,2006 Jason R. Mastaler <jason@mastaler.com>
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

"""General purpose (Pending Queue related) functions."""


import os

from TMDA import Errors
from TMDA import Defaults
from TMDA.Util import msg_as_string, writefile


def create_pending_dir(dirpath=None):
    """ """
    if not dirpath:
	dirpath = Defaults.PENDING_DIR
    if not os.path.exists(dirpath):
	os.makedirs(dirpath, 0700)
    

def create_pending_msg(timestamp, pid, msg):
    """ """
    fname = "%s.%s.msg" % (timestamp, pid)
    # Create ~/.tmda/ and friends if necessary.
    create_pending_dir(Defaults.PENDING_DIR)
    # Write ~/.tmda/pending/TIMESTAMP.PID.msg
    fcontents = msg_as_string(msg)
    fpath = os.path.join(Defaults.PENDING_DIR, fname)
    writefile(fcontents, fpath)
    return fname


def maildirmake(dirpath):
    """ """
    os.makedirs(os.path.join(dirpath, 'cur'), 0700)
    os.mkdir(os.path.join(dirpath, 'new'), 0700)
    os.mkdir(os.path.join(dirpath, 'tmp'), 0700)
    
