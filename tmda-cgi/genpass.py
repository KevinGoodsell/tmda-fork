#!/usr/bin/env python
#
# Copyright (C) 2002 Gre7g Luterman <gre7g@wolfhome.com>
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

"""Simple password generation tool.

Generates an encrypted password entry for use in tmda-cgi's password file.
The password is requested from the terminal and the output is suitable for
concatenation onto a password file with the ">>" pipe.

Usage:  contrib/cgi/genpass.py <user>

Where:
    <user> is the user name
"""

import crypt
import getpass
import random
import sys

def main():
  # Send output to stderr so it wont be piped if they pipe output
  sys.stdout = sys.stderr

  # Did they specify a user name?
  if len(sys.argv) < 2:
    print "Syntax: genpass <user>"
    sys.exit(0)

  # Generate a valid salt
  random.seed()
  SaltSet = "./abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  Salt = SaltSet[random.randrange(0, 64)]
  Salt += SaltSet[random.randrange(0, 64)]

  # Ask for password and verify same
  Pass1 = getpass.getpass()
  Pass2 = getpass.getpass("Re-enter: ")

  if Pass1 != Pass2:
    print "Error: Passwords did not match."
  else:
    # Re-route output to stdout for piping
    sys.stdout = sys.__stdout__
    print "%s:%s" % (sys.argv[1], crypt.crypt(Pass1, Salt))

# This is the end my friend.
if __name__ == '__main__':
    main()
