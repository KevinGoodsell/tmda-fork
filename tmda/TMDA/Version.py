# -*- python -*-

""" Various versioning information."""


import string
import sys


# TMDA version
TMDA = "0.43"

# Python version
PYTHON = string.split(sys.version)[0]

# Platform identifier
try:
    import distutils.util
    PLATFORM = distutils.util.get_platform()
except ImportError:
    PLATFORM = sys.platform

# A summary of all the version identifiers; used primarily for the
# `X-Delivery-Agent' headers.  e.g,
# "TMDA/0.43 (Python 2.1.1; freebsd-4.4-RELEASE-i386)"
ALL = "TMDA/%s (Python %s; %s)" % (TMDA, PYTHON, PLATFORM)
