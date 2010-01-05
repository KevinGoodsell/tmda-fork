#!/usr/bin/env python

import sys
import os
import re

try:
    infile = os.fdopen(3, 'r')
except OSError:
    sys.exit(111)
data = infile.read()

m = re.match(r'(?P<username>[^\0]+)\0(?P<password>[^\0]+)\0', data)
if m is None:
    sys.exit(111)

username, password = m.group('username', 'password')
if username == 'testuser' and password == 'testpassword':
    sys.exit(0)
else:
    sys.exit(1)
