# -*- python -*-

""" Various versioning information."""


import sys


# TMDA version
TMDA = "0.46+"

# Python version
PYTHON = sys.version.split()[0]

# Platform identifier
PLATFORM = sys.platform

# A summary of all the version identifiers.  e.g,
# TMDA/0.46 (Python 2.2; freebsd4)
ALL = "TMDA/%s (Python %s; %s)" % (TMDA, PYTHON, PLATFORM)
