# -*- python -*-

# Hack the path to include the parent directory of the $prefix/TMDA
# package directory.

import os
import sys

progpath = os.path.abspath(sys.argv[0])

if os.path.islink(progpath):
    progpath = os.path.abspath(os.readlink(progpath))

prefix = os.path.split(os.path.dirname(progpath))[0] # '../'

sys.path.insert(1, prefix)
