# -*- python -*-

# Hack the path to include the parent directory of the $prefix/TMDA
# package directory.

import os
import sys

progpath = os.path.abspath(sys.argv[0])

if os.path.islink(progpath):
    progdir = os.path.dirname(progpath)
    linkpath = os.readlink(progpath)
    if os.path.isabs(linkpath):
        progpath = linkpath
    else:
        progpath = os.path.normpath(progdir + '/' + linkpath)

prefix = os.path.split(os.path.dirname(progpath))[0] # '../'

sys.path.insert(1, prefix)
