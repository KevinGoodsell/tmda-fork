#!/usr/bin/env python
#
# Copyright (C) 2003 Gre7g Luterman <gre7g@wolfhome.com>
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

"Local config file editor for tmda-cgi."

import os
import parser
import re
import symbol
from types import *

import CgiUtil
import Template

from TMDA import Defaults
from TMDA import Version

# Regular expression searches
EscapeSearch  = re.compile('(\\")')
EscapeSub     = r"\\\1"
HTMLEscSearch = re.compile('"')
HTMLEscSub    = "&quot;"
CommentSearch = re.compile("^\s*(#.*)?$")
ReturnSearch  = re.compile("\r?\n")
ReturnSub     = "\\\\n"

# Parser symbols allowed in config files, dictionaries, and lists
# Well, all symbols are really ALLOWED, but if we find any outside these sets
# then we will reject them.  It is too risky to go messing with stuff like
# that.
StdSyms = ( 0, 3, 4, 12, symbol.and_expr, symbol.and_test, symbol.arith_expr,
  symbol.atom, symbol.comparison, symbol.expr, symbol.expr_stmt, symbol.factor,
  symbol.not_test, symbol.power, symbol.shift_expr, symbol.simple_stmt,
  symbol.small_stmt, symbol.term, symbol.test, symbol.testlist,
  symbol.xor_expr )
ConfigSyms = StdSyms + ( 1, 2, 7, 8, 9, 10, 11, 14, 22, 26, 27,
  symbol.dictmaker, symbol.listmaker )
DictSyms = StdSyms + ( 1, 11, 14, 26, 27, symbol.dictmaker,
  symbol.file_input, symbol.stmt )
ListSyms = StdSyms + ( 7, 8, 9, 10, symbol.file_input, symbol.listmaker,
  symbol.stmt )

# Track the line number
LineNum = None

def Parse(ASP, AllowSym):
  """Parse an ASP statement.

Given one ASP statement, parse it into text, verify that it is not "dangerous",
and set global variables to track what is assigned where."""

  global LineNum, AssignVar

  if type(ASP) in [StringType, UnicodeType]:
    return ASP
  elif type(ASP[0]) == IntType:
    RetVal = Parse(ASP[1], AllowSym)
    # Symbols < 100 have a single token and a line number
    if ASP[0] < 100:
      LineNum = ASP[-1]
    else:
      # Statements should track the assignment variable
      if ASP[0] == symbol.expr_stmt:
        AssignVar = RetVal
      # Parse the rest of the expression as text
      for x in ASP[2:]:
        RetVal += Parse(x, AllowSym)
    # Verify that the symbol is safe
    if ASP[0] in AllowSym:
      return RetVal
    else:
      # Return an error
      if symbol.sym_name.has_key(ASP[0]):
        Sym = "%s (#%d)" % (symbol.sym_name[ASP[0]], ASP[0])
      else:
        Sym = "#%d" % ASP[0]
      raise KeyError("Unsupported symbol %s found on line %d" % (Sym, LineNum))

def Escape(Value):
  "Escape out the backslashes and quotes."
  Value = EscapeSearch.sub(EscapeSub, Value)
  return '"%s"' % ReturnSearch.sub(ReturnSub, Value)

def Set(Var, Value):
  "Set a variable to a given value."

  global LastLine, Assignments, Config

  if Assignments.has_key(Var):
    Line = Assignments[Var]
  else:
    LastLine += 1
    Line = LastLine
  Config[Line] = '%s=%s' % (Var, Value)

def Show():
  "Edit local config file."

  global AssignVar, Assignments, Config, LineNum, LastLine

  # Load the display template
  T = Template.Template("localconfig.html")
  T["ErrMsg"] = "Displaying requested view. Click on filename to toggle."
  ErrStr = None

  # Toggle modes?
  if Form.has_key("subcmd") and (Form["subcmd"].value == "toggle"):
    if PVars["LocalConfig"] == "Text":
      PVars["LocalConfig"] = "Form"
    else:
      PVars["LocalConfig"] = "Text"
    PVars.Save()

  # Get file
  T["FilePath"] = Defaults.TMDARC
  try:
    F = open(Defaults.TMDARC)
    FileContents = F.readlines()
    F.close()
  except IOError:
    FileContents = []

  # Which view does the user want?  Form or text?
  if PVars["LocalConfig"] == "Form" and Version.TMDA < 1.1:
    # User wants to view the config in form mode.  First we need to dismantle
    # the current config file in a way that we can rebuild it, then we need to
    # verify that it is safe to proceed.

    # Extract any comments & blank lines
    Config = {}
    LastLine = 1
    for LastLine in range(len(FileContents)):
      if CommentSearch.search(FileContents[LastLine]):
        Config[LastLine + 1] = FileContents[LastLine].strip()
    LastLine += 2

    # Test to see if we can do this safely
    FileContents = "".join(FileContents)
    ASP = parser.ast2tuple(parser.suite(FileContents), 1)
    Assignments = {}
    try:
      # Capture each expression
      for Exp in ASP[1:]:
        AssignVar = None
        Line = Parse(Exp[1], ConfigSyms)
        # Track commands in dictionaries
        if Line: Config[LineNum] = Line
        if AssignVar: Assignments[AssignVar] = LineNum
    except (KeyError, parser.ParserError), ErrMsg:
      # Nope.  Not safe!
      T["ErrMsg"] = """Reverted to text mode.
Not safe to proceed in form mode.
%s of current %s""" % (ErrMsg, Defaults.TMDARC)
      PVars["LocalConfig"] = "Text"
      PVars.Save()
    else:
      # We're in form view, hide text view
      T["TextView"]

      # Save changes?
      FormVars = re.split("[,\s]+", T["FormVars"])
      if Form.has_key("subcmd") and (Form["subcmd"].value == "save"):
        try:
          # Go through each variable we're supporting and determine:
          # [1] Is the given value acceptable?
          # [2] Is the new value different than the old?
          for Var in FormVars:
            Parts = Var.split(":")
            # Provided a value?
            if Form.has_key(Parts[0]) and Form[Parts[0]].value.strip():
              Value = Form[Parts[0]].value
              if len(Parts) == 2:
                # Lists and dictionaries must be tested for dangerous code
                ASP = parser.ast2tuple(parser.suite(Value), 1)
                if Parts[1] == "L":
                  Value = Parse(ASP, ListSyms)
                else:
                  Value = Parse(ASP, DictSyms)
              else:
                # Integers are okay as-is, strings must be escaped
                if (len(Parts) == 1) or (Parts[1] != "I"):
                  Value = Escape(Value)
            # If no value is given, use None
            else:
              Value = "None"
            # Has value been changed?
            if vars(Defaults)[Parts[0]] != eval(Value):
              Set(Parts[0], Value)
              vars(Defaults)[Parts[0]] = eval(Value)

          # Check code for syntax errors BEFORE saving
          try:
            # Re-assemble config
            Temp   = Config
            Config = ""
            Lines  = Temp.keys()
            Lines.sort()
            for Line in Lines: Config += Temp[Line] + "\n"

            # Try to execute it
            try:
              exec(Config)
            except (ImportError, NameError):
              pass

            # Looks okay, so save it
            T["ErrRow"]
            F = open(Defaults.TMDARC, "w")
            F.write(Config)
            F.close()
          except SyntaxError, (ErrStr, Details):
            T["ErrStr"] = "SyntaxError: line %d, char %d<br>(%s)" % Details[1:4]
        except (KeyError, parser.ParserError), ErrStr:
          # Don't like the look of this var!
          T["ErrStr"] = """<nobr>Contents of variable %s look "unsafe".<br>
%s</nobr>""" % (Parts[0], ErrStr)

      # Display current values
      for Var in FormVars:
        Parts = Var.split(":")
        Value = vars(Defaults)[Parts[0]]
        if Value == None:
          Value = ""
        else:
          if len(Parts) == 2:
            Value = repr(Value)
          else:
            Value = str(Value)
        T[Parts[0]] = HTMLEscSearch.sub(HTMLEscSub, Value)
        if len(Parts) > 2:
          for Part in Parts[1:]:
            if str(Value) == Part:
              T["%s%sSelected" % (Parts[0], Part)] = " selected"
              T["%s%sChecked" % (Parts[0], Part)] = " checked"
            else:
              T["%s%sSelected" % (Parts[0], Part)] = ""
              T["%s%sChecked" % (Parts[0], Part)] = ""
  else:
    FileContents = "".join(FileContents)

  if PVars["LocalConfig"] == "Text" or Version.TMDA >= 1.1:
    # We're in text view, hide form view
    T["FormView"]
    T["FileContents"] = FileContents

    # Hide save button?
    if PVars[("NoOverride", "MayEditLocalConfig")][0].lower() == "n":
      T["SaveButton"]

  # Saving with text method?
  if (PVars["LocalConfig"] == "Text") and Form.has_key("subcmd") and \
    (Form["subcmd"].value == "save") and \
    (PVars[("NoOverride", "MayEditLocalConfig")][0].lower() == "y"):
    try:
      # Make sure the list is properly formatted
      Config = re.sub("\r\n", "\n", Form["config"].value)
      Config = re.sub("\n*$", "", Config)
      Config += "\n"

      # Check code for syntax errors BEFORE saving
      try:
        try:
          exec(Config)
        except (ImportError, NameError):
          pass
        T["ErrRow"]
        F = open(Defaults.TMDARC, "w")
        F.write(Config)
        F.close()
      except SyntaxError, (ErrStr, Details):
        T["ErrStr"] = "SyntaxError: line %d, char %d<br>(%s)" % Details[1:4]
      T["FileContents"] = Config
    except IOError, ErrStr:
      CgiUtil.TermError("Unable to save config file.",
      "Insufficient privileges", "save config", "%s<br>%s" % (ErrStr,
      CgiUtil.FileDetails("Local config", Defaults.TMDARC)),
      "Change file permissions on <tt>%s</tt>" % Defaults.TMDARC)

  # Did we find any errors?
  if ErrStr:
    T["PathRow"]  # Hide path
  else:
    T["ErrRow"]   # Hide error

  # Display template
  print T
