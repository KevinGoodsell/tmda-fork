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
    self.test_buttons()
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
    name     = 'subtopic%d' % subtopic
    normal   = '%%(ThemeDir)s/dyn_buttons/%s.png' % name
    high     = '%%(ThemeDir)s/dyn_buttons/h-%s.png' % name
    alt      = ' - %s' % sidebar[i][1].replace('/', ' ')
    height   = 14 * len(sidebar[i][1].split('/'))
    dom_src  = 'document.images.%s.src' % name
    mouse    = '''onmouseover="%s='%s'"
onmouseout="%s='%s'"''' % (dom_src, high, dom_src, normal)
    img_attr = '''border="0" alt="%s" title="%s" width="194" height="%d"
name="%s"''' % (alt, alt, height, name)
    img_tag  = '<img src="%s" %s>' % (normal, img_attr)
    hi_tag   = '<img src="%s" %s>' % (high, img_attr)
    preload  = 'var %s = new Image();\n%s.src = "%s";\n' % \
        (name, name, high)
    sidebar[i] = (sidebar[i][0], img_tag, (mouse, hi_tag, preload))
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

  def test_buttons(self):
    try:
      if self.buttons == pickle.load(open('buttons.p')): return
    except IOError:
      pass
    pickle.dump(self.buttons, open('buttons.p', 'w'))
    os.chdir('..')
    button = 1
    y = 21
    for name in self.buttons['topics']:
      os.system('../../../button_maker/compose.pl '
        'button_templates/layout1_r%d_c1.gif 7 %d 18 "%s" '
        'dyn_buttons/layout1_r%d_c1.png' % (button, y, name, button))
      os.system('../../../button_maker/compose.pl '
        'button_templates/layout1_r%d_c1.gif 7 %d 18H "%s" '
        'dyn_buttons/layout1_r%d_c1_h.png' % (button, y, name, button))
      button += 1
      y = 6
    button = 1
    Subtopics = {}
    for name in self.buttons['subtopics']:
      os.system('../../../button_maker/compose.pl -w 194 -i 20 left_bg.gif '
        '7 0 14 "%s" dyn_buttons/subtopic%d.png' % (name, button))
      os.system('../../../button_maker/compose.pl -w 194 -i 20 left_bg.gif '
        '7 0 14H "%s" dyn_buttons/h-subtopic%d.png' % (name, button))
      Subtopics[name] = \
      {
        "width": 194, "height": 14,
        "fn": "dyn_buttons/subtopic%d.png" % button,
        "hfn": "dyn_buttons/h-subtopic%d.png" % button
      }
      button += 1
    pickle.dump(Subtopics, open('subtopics.p', 'w'))
    os.chdir('template')

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
    return '''<img src="%(ThemeDir)s/title.png" width="341" height="135"
alt="TMDA (http://tmda.net) CGI Interface" title="TMDA (http://tmda.net) CGI Interface">'''

  def get_corner(self):
    # It is important not to have newlines between the img tag and the end
    # anchor and end center tags, otherwise layout gets messed up
    return '<img src="%(ThemeDir)s/corner.gif" width="194" height="135" alt="">'

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

  def get_corner_bgcolor(self):
    return '#7B7CB6'

  def get_corner_metrics(self):
    return 'width="194" height="135"'

  def use_spacers(self):
    return 0

  def get_banner_metrics(self):
    return 'height="135" valign="top" background="%(ThemeDir)s/top_bg.gif" bgcolor="#7B7CB6"'

  def get_sidebar_table_metrics(self):
    return 'width="194" background="%(ThemeDir)s/left_bg.gif" bgcolor="#7B7CB6"'

  def get_sidebar_metrics(self):
    return 'cellspacing="0" cellpadding="0"'

  def get_category(self, item, itemnum):
    # Add some scripting for rollovers
    temp = len(self.rollover)
    self.rollover += '''  var x%d = new Image();
x%d.src = "%%(ThemeDir)s/dyn_buttons/layout1_r%d_c1_h.png";
''' % (temp, temp, itemnum)
    temp = '''<td><a href="%s"
onmouseover="document.images.x%d.src='%%(ThemeDir)s/dyn_buttons/layout1_r%d_c1_h.png'"
onmouseout="document.images.x%d.src='%%(ThemeDir)s/dyn_buttons/layout1_r%d_c1.png'"><img
src="%%(ThemeDir)s/dyn_buttons/layout1_r%d_c1.png" name="x%d" height="''' % (
self.assoc[item], temp, itemnum, temp, itemnum, itemnum, temp)
    if itemnum == 1:
      temp += "50"
    elif itemnum > 6:
      temp += "39"
    else:
      temp += "35"
    return temp + ('" width="194" border="0" alt="%s" title="%s"></a></td>' % (item,item))

  def get_item(self, url, text, extra):
    if url is None:
      s = extra[1]
    else:
      s = '<a href="%s" %s>%s</a>' % (url, extra[0], text)
      self.rollover += extra[2]
    return '<tr><td>%s</td></tr>' % (s)

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
    return '''bgcolor="#FFFFFF" %s height="100%%" border="0"
cellspacing="0" cellpadding="0"><tr><td valign="top"><table class="matte"
width="100%%" height="100%%" border="0" cellspacing="0" cellpadding="0"><tr>
<td valign="top"><table width="100%%"''' % Width

  def get_body_close(self):
    return '</table></td></tr></table></td></tr>'

  def finish_all(self):
    # rollover preloader
    print '''%s}
//-->
</script>
</body></html>''' % self.rollover
