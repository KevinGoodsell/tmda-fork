#!/usr/bin/env python
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
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

"""
An unsupported Python distutils setup configuration file for TMDA.
Contributed by Skip Montanaro <skip@pobox.com>

The net effect of running "python setup.py install" is to:
 * install the TMDA package in $prefix/lib/.../site-packages
 * install the confirm templates in $prefix/lib/TMDA-NNN/templates
 * install the sample.tmdarc file in $prefix/lib/TMDA-NNN/etc
 * install the HTML documentation in $prefix/share/doc/TMDA-NNN
 * install the scripts in bin and contrib in $prefix/bin
"""

import distutils.core
import os
import glob

PKG_NAME = "TMDA"
PKG_VERSION = "0.48"
PKG_FULL_NAME = "%s-%s" % (PKG_NAME, PKG_VERSION)

distutils.core.setup(name=PKG_NAME,
                     version=PKG_VERSION,
                     description="user-level UCE intrusion prevention",
                     author="Jason R. Mastaler",
                     author_email="jason@mastaler.com",
                     licence="GPL",
                     url="http://tmda.sourceforge.net/",
                     packages=['TMDA'],
                     scripts=['bin/tmda-address',
                              'bin/tmda-check-address',
                              'bin/tmda-clean',
                              'bin/tmda-filter',
                              'bin/tmda-inject',
                              'bin/tmda-keygen',
                              'bin/tmda-rfilter',
                              'bin/tmda-sendmail',
                              'contrib/list2cdb',
                              'contrib/list2dbm',
                              'contrib/printcdb',
                              'contrib/printdbm'],
                     data_files=[(os.path.join('lib',
                                               PKG_FULL_NAME,
                                               'templates'),
                                  ['templates/confirm_accept.txt',
                                   'templates/confirm_request.txt']),
                                 (os.path.join('lib',
                                               PKG_FULL_NAME,
                                               'etc'),
                                  ['contrib/sample.tmdarc']),
                                 (os.path.join('share', 'doc', PKG_FULL_NAME),
                                  glob.glob('htdocs/*.html'))])
