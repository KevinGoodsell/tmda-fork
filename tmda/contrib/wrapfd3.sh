#!/bin/sh
#
# -----------------------------------------------------------------------------
#
# wrapfd3.sh - A wrapper for python program which use Auth.py to guarantee
#              that File Discriptor 3 is available.
#
# Version: 0.1                                            
#
# Copyright (C) 2003 Jim Ramsay <i.am@jimramsay.com>
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
#
# -----------------------------------------------------------------------------
#  
# Usage and rationale:
# ===================
#
# This wrapper is to be used in systems where FD3 is used by the threading
# library (FreeBSD is known to be affected, among others)
#
# It is designed to be used around any python program which needs to access FD3
# for the purpose of using a checkpassword program from within Auth.py.
# Currently no programs require this wrapper, as tmda-ofmipd does not yet use
# Auth.py, and  tmda-cgi which does already has its own wrapper.
#
# In the future this may be neccessary to run tmda-ofmipd on affected systems.
#
# To see if your system is affected, run "python" interactively, then issue
# the following commands:
#
#   >>> import os
#   >>> a,b = os.pipe()
#   >>> a
#
# If "a" is 3, you are not affected by this problem.  If "a" is something other
# than 3, try the following:
#
#   >>> os.dup2(a,3)
#
# If this succeeds, you are also not affected by this problem.  However, if you
# get "OSError: [Errno 9] Bad file descriptor", you are affected, and this
# wrapper is for you.
#
# Please note that if your system is not affected, running this wrapper will
# not be harmful.  Probably.
#
# -----------------------------------------------------------------------------
#
# Release History:
# ===============
#
# 0.1 - First release
#
# -----------------------------------------------------------------------------

# Make sure that there's at least one arg, and check for "help"
if [ -z "$1" -o "$1" = "-h" -o "$1" = "--help" ]; then
    echo "FD3 Wrapper"
    echo ""
    echo "  Wraps a program with FD#3 open"
    echo "  (so it is not used by the operating system)"
    echo "  For more information, please see the comments within this file"
    echo ""
    echo "Usage:"
    echo ""
    echo "  `basename $0` program [arg1 ...]"
    echo ""
    exit 1
fi

# Alright - exec the program keeping FD3 accesable
exec $@ 3</dev/null
