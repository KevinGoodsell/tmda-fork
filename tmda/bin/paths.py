# -*- python -*-

# Hack the path to include the parent directory of the $prefix/TMDA
# package directory.

import os
import sys

program = sys.argv[0]

try:
    progpath = os.path.realpath(program)
except AttributeError:
    progpath = os.path.abspath(program)

prefix = os.path.split(os.path.dirname(progpath))[0] # '../'

sys.path.insert(1, prefix)
