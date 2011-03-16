#!/usr/bin/env python

import sys

print 'FAKE SENDMAIL ARGS:', sys.argv

for line in sys.stdin:
    print line,

sys.exit(0)
