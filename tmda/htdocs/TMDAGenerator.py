# -*- python -*-
#
# Copyright (C) 2001,2002,2003 Jason R. Mastaler <jason@mastaler.com>
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

"""Generates the TMDA documentation style
"""

import os
import time

from Skeleton import Skeleton
from Sidebar import Sidebar, BLANKCELL
from Banner import Banner
from HTParser import HTParser
from LinkFixer import LinkFixer



sitelinks = [
    ('%(rootdir)s/index.html', 'TMDA Homepage', '<br>[\
    <a href="http://www.au.tmda.net/">AU</a> |\
    <a href="http://www.us.tmda.net/">US</a> \
    mirror ]'),
    ('http://sourceforge.net/projects/tmda', 'TMDA @ SourceForge'),
    ]


class TMDAGenerator(Skeleton, Sidebar, Banner):
    AUTHOR = 'Jason R. Mastaler'
    EMAIL = 'jason@mastaler.com'

    def __init__(self, file, rootdir, relthis):
        root, ext = os.path.splitext(file)
        html = root + '.html'
        p = self.__parser = HTParser(file, self.AUTHOR, self.EMAIL)
        f = self.__linkfixer = LinkFixer(html, rootdir, relthis)
        self.__body = None
        self.__cont = None
        # Calculate the sidebar links, adding a few of our own.
        self.__d = {'rootdir': rootdir}
        p.process_sidebar()
        p.sidebar.append(BLANKCELL)
        self.__linkfixer.massage(p.sidebar, self.__d)
        Sidebar.__init__(self, p.sidebar)
        #p.sidebar.append(BLANKCELL)
        copyright = self.__parser.get('copyright', '2001-%d' %
                                      time.localtime()[0])
        p.sidebar.append((None, '&copy; ' + copyright))
        #last_modified = self.__parser.get('last_modified', '%s' %
        #                              time.asctime(time.gmtime(time.time())))
        #p.sidebar.append('Updated: ' + last_modified)
        # Fix up our site links, no relthis because the site links are
        # relative to the root of our web pages.
        sitelink_fixer = LinkFixer(f.myurl(), rootdir)
        sitelink_fixer.massage(sitelinks, self.__d, aboves=1)
        Banner.__init__(self, sitelinks)
        # kludge!
        for i in range(len(p.sidebar)-1, -1, -1):
            if p.sidebar[i] == 'Email Us':
                p.sidebar[i] = 'Author'
                break

                
    def get_title(self):
        return self.__parser.get('title')

    def get_sidebar(self):
        if self.__parser.get('wide-page', 'no').lower() == 'yes':
            return None
        return Sidebar.get_sidebar(self)

    def get_banner(self):
        return Banner.get_banner(self)

    def get_banner_attributes(self):
        return 'CELLSPACING=0 CELLPADDING=0'

    def get_corner(self):
        # It is important not to have newlines between the img tag and the end
        # anchor and end center tags, otherwise layout gets messed up
        return '''<center><font size="+2"
        >&gt;&gt;&gt;&nbsp;TMDA&nbsp</font></center>'''

    def get_body(self):
        self.__grokbody()
        return self.__body

    def get_cont(self):
        self.__grokbody()
        return self.__cont

    def __grokbody(self):
        if self.__body is None:
            text = self.__parser.fp.read()
            i = text.find('<!--table-stop-->')
            if i >= 0:
                self.__body = text[:i]
                self.__cont = text[i+17:]
            else:
                # there is no wide body
                self.__body = text


    # python.org color scheme overrides
    def get_lightshade(self):
        return '#cccccc'
        
    def get_mediumshade(self):
        return '#9862cb'

    def get_darkshade(self):
        return '#191970'

    def get_corner_bgcolor(self):
        return '#afeeee'
    
# jython.org color scheme
#     def get_lightshade(self):
#         return '#cccccc'
#     def get_mediumshade(self):
#         return '#9862cb'
#     def get_darkshade(self):
#         return '#666699'
#     def get_corner_bgcolor(self):
#         return '#cccccc'
