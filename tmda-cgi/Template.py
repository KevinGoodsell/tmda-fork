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

"Use this module to load and manipulate HTML templates."

# Instantiate this object as such:
#   T = Template("<filename>")
#
# The template will be loaded and may be printed as such:
#   print T
#
# This will substitute any variables encoded in the HTML such as %(StringVar)s
# and %(NumVar)d.  You should not double up any regular percent signs to keep
# them from expanding.  For example, <table width=100%> is fine,
# <table width=100%%> is not.
#
# Standard dictionary assignment statements will define these substituted
# variables*:
#   T["StringVar"] = "foo"
#   T["NumVar"] = 7
#
# You may embed variables in the HTML template as such:
#   <!-- var: Column --><td>%(Value)s</td><!-- /var -->
#
# Or:
#   <!-- var: Column="5" -->
#
# The latter form will be extracted as a string.  You cannot use the Add() and
# Clear() functions for this form.
#
# You may add a comment in the ending tag if you wish:
#   <!-- var: Column --><td>%(Value)s</td><!-- /var (Column) -->
#
# To replace these embedded variables, you must first extract them:
#   C = T["Column"]
#
# This will remove the entire block from the HTML template.  To add these
# sections back in with your own values, use the Add() member:
#
#   C.Add({"Column": "bar"})
#
# The dictionary parameter is optional.  If omitted, the standard dictionary is
# used in the substitution process (see * above).  Note that ALL instantiations
# of Template share the same standard dictionary.  If you add a value to one,
# it is available to all.
#
# Embedded variables may be nested, but to do this, you must extract the
# innermost variables first.  For example, if your HTML in variable T included:
#
# <!-- var: Row --><tr>
#   <!-- var: Column --><td>%(Value)s</td><!-- /var (Column) -->
# </tr><!-- /var (Row) -->
#
# You could parse this and create a 2 x 2 table with:
#
# C = T["Column"]
# R = T["Row"]
# C.Add({"Value": "UL"})
# C.Add({"Value": "UR"})
# R.Add()
# C.Clear()  # So "UL" & "UR" won't be added a second time
# C.Add({"Value": "LL"})
# C.Add({"Value": "LR"})
# R.Add()
#
# This would replace the HTML with:
#
# <tr>
#   <td>UL</td><td>UR</td>
# </tr>
# <tr>
#   <td>LL</td><td>LR</td>
# </tr>
#
# You must add from the inside out.
#
# Embedded variables may also be replaced with text, however, you must do this
# in a two step process to keep from merely setting a standard dictionary
# index with the same name as the embedded variable.  For example, suppose you
# had the following HTML:
#
# <center><!-- var: NoSubmit --><input type="submit"><!-- /var --></center>
#
# By executing the following code:
#
# T["NoSubmit"]
# T["NoSubmit"] = "Form may not be submitted."
#
# Would replace the HTML with:
#
# <center>Form may not be submitted.</center>

import copy
import re
import sys
from types import StringType

# Module globals
SentHeaders = 0

def Debug(Str):
  "Output a debugging string."

  global SentHeaders

  if not SentHeaders: sys.stdout.write("Content-Type: text/html\n\n")
  SentHeaders = 1
  print Str

class Template:
  # Members global across all instantiations:
  Dict            = {"CharSet": "utf-8"}
  BaseDir         = "."
  VarSearchStr    = '<!--\s*var:\s*%s(?:="([^"]+)")?\s*-->'
  VarEndSearch    = re.compile("<!--\s*/var[^-]*-->", re.I)
  LonePctSearch   = re.compile("([^%])%([^(%])")
  LonePctRepl     = r"\1%%\2"
  SearchDict      = {}
  BeenExpanded    = 0

  def __init__ \
  (
    self, Filename = None, BoilerPlate = None, SubTemplate = None, Name = None
  ):
    "Constructor."
    self.BoilerPlate = BoilerPlate
    self.Name = Name
    if SubTemplate:
      self.HTML = SubTemplate
    else:
      self.HTML = []
    if (Filename):
      F = open("%s/%s" % (self.BaseDir, Filename))
      self.HTML = [self.LonePctSearch.sub(self.LonePctRepl, F.read())]
      F.close()
    self.Items = {}

  def __setitem__(self, Index, Value):
    "Assign a substitution variable."
    if self.Items.has_key(Index):
      self.Items[Index].HTML = [Value]
    else:
      self.Dict[Index] = Value

  def __str__(self):
    "Convert to string for printing in browser. (Adds content-type header)"

    global SentHeaders

    if not SentHeaders:
      sys.stdout.write \
      (
        "Content-Type: text/html; charset=%(CharSet)s\n\n" % self.Dict
      )
    SentHeaders = 1

    RetVal = ""
    for HTML in self.HTML:
      if type(HTML) == StringType:
        if self.BeenExpanded:
          RetVal += HTML
        else:
          RetVal += self.LonePctSearch.sub(self.LonePctRepl, HTML) % self.Dict
      else:
        RetVal += str(HTML)
    return RetVal

  def UpdateItems(self, Target):
    for i in range(len(self.HTML)):
      if type(self.HTML[i]) != StringType:
        if self.HTML[i].Name:
          self.HTML[i].BoilerPlate.UpdateItems(self.HTML[i])
          Target.Items[self.HTML[i].Name] = self.HTML[i]
        else:
          self.HTML[i].UpdateItems(Target)

  def __getitem__(self, Var):
    """Find and extract an embedded variable in template."""

    # Have we found this item before?
    if self.Items.has_key(Var):
      return self.Items[Var]

    # Do we have a search compiled yet?
    if not self.SearchDict.has_key(Var):
      self.SearchDict[Var] = re.compile(self.VarSearchStr % Var, re.I)

    # Find the start tag
    for i in range(len(self.HTML)):
      if type(self.HTML[i]) == StringType:
        Match = self.SearchDict[Var].search(self.HTML[i])
        if Match:
          # Is it an all-in-one tag?
          if Match.group(1):
            # Found start tag, split off text before and after it
            self.HTML[i] = \
              self.HTML[i][:Match.start()] + self.HTML[i][Match.end():]
            return Match.group(1)
          else:
            # Found start tag, split off text before it
            self.HTML[i:i+1] = \
              [self.HTML[i][:Match.start()], self.HTML[i][Match.end():]]
            # Now search for the end tag
            for j in range(i+1, len(self.HTML)):
              if type(self.HTML[j]) == StringType:
                Match = self.VarEndSearch.search(self.HTML[j])
                if Match:
                  # Found end tag, split off text after it
                  self.HTML[j:j+1] = \
                    [self.HTML[j][:Match.start()], self.HTML[j][Match.end():]]
                  # Replace contents with a template
                  Extracted = Template(SubTemplate = self.HTML[i+1:j+1])
                  BoilerPlate = Template(BoilerPlate = Extracted, Name = Var)
                  BoilerPlate.UpdateItems(BoilerPlate)
                  self.HTML[i+1:j+1] = [BoilerPlate]
                  self.UpdateItems(self)
                  return self.HTML[i+1]
          raise KeyError, "Can't find end tag for variable: %s" % Var
      else:
        RetVal = self.HTML[i][Var]
        if RetVal:
          self.UpdateItems(self)
          return RetVal
    return None

  def Expand(self, Dict):
    "Expand any %(<name>)s references in self."
    for i in range(len(self.HTML)):
      if type(self.HTML[i]) == StringType:
        if not self.BeenExpanded:
          self.HTML[i] = \
            self.LonePctSearch.sub(self.LonePctRepl, self.HTML[i]) % Dict
      else:
        self.HTML[i].Expand(Dict)
    self.BeenExpanded = 1
    return self

  def Add(self, Dict = None):
    "Add to the template using the boilerplate."
    if not Dict: Dict = self.Dict
    self.HTML.append(copy.deepcopy(self.BoilerPlate))
    self.Expand(Dict)

  def Clear(self):
    self.HTML = []
