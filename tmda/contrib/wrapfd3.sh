#!/bin/sh
#
# This file is part of TMDA
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
