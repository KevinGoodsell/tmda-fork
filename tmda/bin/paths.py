# -*- python -*-

# Hack the path to include the parent directory of the $prefix/TMDA
# package directory.

import os
import sys

prefix = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))[0] # '../'
sys.path.insert(1,prefix)
