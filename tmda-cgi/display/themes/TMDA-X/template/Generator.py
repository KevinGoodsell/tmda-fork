# -*- python -*-
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

"""Generates the TMDA documentation style
"""

import os
import pickle
import re
import string
import sys
import time
from types import StringType

# Constants
FindCmd = re.compile('\?cmd=([^&"]+)')

XtraSub = \
[
  'whitelist', 'white', 'blacklist', 'black', 'confirmed', 'confirm', 'revoked',
  'work', 'family', 'friends', 'accept', 'deny', 'whitelist_confirmed', 'other'
]
PageWidth = \
{
  '': 'width="700"', 'list.html': '', 'prog_err.html': '', 'pending.html': '',
  'view.html': 'width="800"'
}

from ht2html import __version__

if __version__ < '2.1':
  print "ERROR!  ht2html version 2.1 required."
  sys.exit(1)

from Skeleton import Skeleton
from Sidebar import Sidebar, BLANKCELL
from Banner import Banner
from HTParser import HTParser
from LinkFixer import LinkFixer

class Generator(Skeleton, Sidebar, Banner):
  def __init__(self, file, rootdir, relthis):
    root, ext = os.path.splitext(file)
    self.html = root + '.html'
    p = self.__parser = HTParser(file)
    f = self.__linkfixer = LinkFixer(self.html, rootdir, relthis)
    self.__body = None
    self.__cont = None
    # Calculate the sidebar links, adding a few of our own.
    self.__d = {'rootdir': rootdir}
    p.process_sidebar()
    p.sidebar = p.sidebar[:-2]
    self.make_assoc(p.sidebar)
    self.find_buttons(p.sidebar)
    self.collapse_links(p.sidebar, self.html)
    if type(p.sidebar[-1]) != StringType:
        p.sidebar = p.sidebar[:-1]
    Sidebar.__init__(self, p.sidebar)
    Banner.__init__(self, ())
    # Rollover script
    self.rollover = '''<script>
<!--
function Preloader()
{
'''

  def do_button(self, sidebar, i, subtopic):
    self.buttons['subtopics'].append(sidebar[i][1])
    preload = ""
    name = '<li>%s' % sidebar[i][1].replace('/', ' ')
    linkClass = "class=\"sidebarSubLink\""
    activeName = "<span class=\"sidebarActive\">%s</span>" % name
    sidebar[i] = (sidebar[i][0], name, (linkClass, activeName, preload))
    return subtopic + 1

  def find_buttons(self, sidebar):
    subtopic = 1
    self.buttons = {'topics': [], 'subtopics': []}

    # Collapse E-mail
    try:
      i = 0
      while 1:
        if (type(sidebar[i]) != StringType) and (sidebar[i][1] == "E-mail"):
          #sidebar[i] = (sidebar[i][0], "   E-mail")
          subtopic = self.do_button(sidebar, i, subtopic)
          if self.html == "view.html":
            sidebar[i-1:i] = []
          else:
            sidebar[i:i+1] = []
        i += 1
    except IndexError:
      pass

    for i in range(len(sidebar)):
      if type(sidebar[i]) == StringType:
        self.buttons['topics'].append(sidebar[i])
      else:
        if len(sidebar[i][1]) and sidebar[i][1][0] == "%":
          sidebar[i] = (sidebar[i][0], None, (None, sidebar[i][1]))
        elif len(sidebar[i]) == 2:
          if sidebar[i][1]: subtopic = self.do_button(sidebar, i, subtopic)
    for i in XtraSub:
      self.buttons['subtopics'].append(i)
    self.copyright = sidebar[-1]

  def make_assoc(self, sidebar):
    self.assoc = {}
    topic = ""
    for i in range(len(sidebar)):
      if type(sidebar[i]) == StringType:
        topic = sidebar[i]
      else:
        if topic != "":
          self.assoc[topic] = sidebar[i][0]
          topic = ""

  def collapse_links(self, sidebar, html):
    search_topic = 0
    try:
      while 1: # check sub links to see if we're one of them
        i = search_topic + 1
        while 1:
          if type(sidebar[i]) == StringType:
            # found next subject, so let's collapse this one
            search_topic += 1
            while type(sidebar[search_topic]) != StringType:
              sidebar[search_topic:search_topic + 1] = []
            break
          else:
            if sidebar[i][0]:
              Match = FindCmd.search(sidebar[i][0])
              if Match and (('%s.html' % Match.group(1)) == html):
                if len(sidebar[i]) > 2:
                  # deactivate us
                  sidebar[i] = (None, sidebar[i][1], sidebar[i][2])
                  # found us, collapse others
                  while type(sidebar[i]) != StringType: i += 1
                while 1:
                  if type(sidebar[i]) != StringType:
                    sidebar[i:i+1] = []
                  else:
                    i += 1
            i += 1
    except IndexError:
      pass

  def get_title(self):
    return self.__parser.get('title')

  def get_sidebar(self):
    if self.__parser.get('wide-page', 'no').lower() == 'yes':
      return None
    return Sidebar.get_sidebar(self)

  def get_banner(self):
    return '''<map name="bannerMap" id="bannerMap">
<area href="http://tmda.net" shape="RECT" Coords="328,111,456,134" title="http://tmda.net">
</map><img src="%(ThemeDir)s/banner.png" usemap="#bannerMap" width="457" height="135" border=0>'''
    return "<span class=\"mainTitle\">TMDA<sup>cgi</sup></span>"

  def get_corner(self):
    # It is important not to have newlines between the img tag and the end
    # anchor and end center tags, otherwise layout gets messed up
    return '<img src="%(ThemeDir)s/corner.png" alt="[Lighthouse]">'

  def get_body(self):
    self.__grokbody()
    tmp = '''<table width="100%%" height="100%%" border=0 cellspacing=0 cellpadding=0>
<tr><td bgcolor=#000000 height="20" align="left" class="banner2"><img src="%%(ThemeDir)s/banner2.png"</td></tr>
<tr><td class="mainContent" valign="top">
%s
</tr></td>
</table>''' % self.__body
    return tmp

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

  def get_corner_bgcolor(self):
    return '#76B2F6'

  def get_corner_metrics(self):
    return 'align="right" valign="bottom"'

  def use_spacers(self):
    return 0

  def get_banner_metrics(self):
    return 'height="135" valign="bottom" bgcolor="#76B2F6"'

  def get_sidebar_table_metrics(self):
    return 'width="130" bgcolor="#000000"'

  def get_sidebar_metrics(self):
    return 'cellspacing="0" cellpadding="0"'

  def get_category(self, item, itemnum):
    return "<td class=\"sidebar\"><A href=\"%s\" class=\"sidebarMainLink\">%s</a></td>" % ( self.assoc[item], item )

  def get_item(self, url, text, extra):
    if url is None:
      s = extra[1]
    else:
      s = '<a href="%s" %s>%s</a>' % (url, extra[0], text)
      self.rollover += extra[2]
    return '<tr class="sidebar"><td>%s</td></tr>' % (s)

  def get_stylesheet(self):
    return '%(ThemeDir)s/styles.css'

  def get_body_attributes(self):
    return 'onload="Preloader()"'

  def get_bgcolor(self):
    return '#A6A6B3'

  def get_charset(self):
    return '%(CharSet)s'

  def get_body_metrics(self):
    Width = 'width="700"'
    if PageWidth.has_key(self.html):
      Width = PageWidth[self.html]
    else:
      Width = PageWidth['']
    return '''bgcolor="#FFFFFF" width="100%%" height="100%%" border="0"
cellspacing="0" cellpadding="0"'''

  def get_body_close(self):
    return ''

  def finish_all(self):
    # rollover preloader
    print '''%s}
//-->
</script>
</body></html>''' % self.rollover
