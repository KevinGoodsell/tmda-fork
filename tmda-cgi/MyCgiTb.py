# -*- python -*-
#
# Copyright (C) 2003 Gre7g Luterman <gre7g@wolfhome.com>
#
# This file is part of tmda-cgi.
#
# tmda-cgi is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  A copy of this license should
# be included in the file COPYING.
#
# tmda-cgi is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with tmda-cgi; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""A wrapper around cgitb that places errors in our framework and uses our 
colors."""

import sys

import Template

# Customizable colors to look for in prog_err.html
ColorSwap = \
{
  "Lavender": "#d8bbff", "Pink": "#ffccee",
  "Purple":   "#6622aa", "Grey": "#909090"
}
ErrTemplate = None

def CgiTbReset():
  "Replacement function for cgitb.reset()"
  return ""

def ColorReplacer((etype, evalue, etb), context=5):
  "Stub function for cgitb.html()"

  # Generate standard page
  HTML = CgiTbHtml((etype, evalue, etb), context)

  # Load error framework
  T = Template.Template(ErrTemplate)

  # Swap colors in ColorSwap with those specified in template
  for Color in ColorSwap.keys():
    HTML = HTML.replace(ColorSwap[Color], T[Color])

  # Save HTML
  T["ErrorMessage"] = HTML

  # Return new, frameworked page
  return str(T)

# Try to import cgitb (not present in Python before version 2.2)
try:
  import cgitb

  # Override functions with stubs
  CgiTbHtml = cgitb.html
  cgitb.html = ColorReplacer
  cgitb.reset = CgiTbReset

  # Enable traceback
  cgitb.enable()
except ImportError:
  pass
