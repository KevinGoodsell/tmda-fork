# -*- python -*-
#
# Copyright (C) 2001-2007 Jason R. Mastaler <jason@mastaler.com>
#
# Authors: Tim Legant <tim@catseye.net> and
#          Jason R. Mastaler <jason@mastaler.com>
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
TMDA filter file parser.

Filter file syntax documented in htdocs/config-filter.html
"""


import os
import popen2
import re
import string
import sys
import time
import types

import Defaults
import Util


# exception classes
class Error(Exception):
    def __init__(self, msg=''):
        self._msg = msg
        Exception.__init__(self, msg)


class ParsingError(Error):
    """Exception raised on parsing errors in the filter file."""
    def __init__(self, filename):
        Error.__init__(self, 'Filter contains parsing errors: %s' % filename)
        self.filename = filename
        self.errors = []

    def append(self, lineno, errmsg):
        self.errors.append((lineno, errmsg))

    def __repr__(self):
        msg = self._msg
        for err in self.errors:
            msg += '\n\t[line %2d]: %s' % err
        return msg
    __str__ = __repr__


class MatchError(Error):
    """Exception raised in firstmatch when attempting to match rule."""
    def __init__(self, lineno, errmsg):
        Error.__init__(self, '[line %2d]: %s' % (lineno, errmsg))


class Macro:
    """Macro definition as parsed by the filter parser."""

    macro_words = re.compile(r'([_a-zA-Z][_\w]*)')
    macro_chars = '_' + string.digits + string.letters

    def __init__(self, name):
        self.name = name
        self.parms = []
        self.definition = ''

    def set_definition(self, definition):
        """Store the text to be substituted."""
        if not definition:
            errstr = '"%s": macro name without definition' % self.name
            raise Error, errstr
        self.definition = definition

    def has_parms(self):
        """Return true if the macro expects arguments."""
        return len(self.parms)

    def findname(self, text):
        """Find the macro name in 'text' or raise ValueError.

        If the name is found, return two strings: the text preceding the
        name and the text following the name.
        
        """
        pattern = r'(?:^|[^_\w])(' + self.name + r')(?:[^_\w]|$)'
        re_macro = re.compile(pattern, re.IGNORECASE)
        mo = re_macro.search(text)
        if not mo:
            raise ValueError
        (start, end) = mo.span(1)
        return (text[:start], text[end:])

    def getargs(self, text):
        """Parse comma-separated text from between parens - '(' and ')'.

        Return list of strings and the text following the right paren - ')'.
        If no parens are found, return an empty argument list and the
        original text.
        
        """
        args = []
        tmp_text = text.lstrip()
        if tmp_text.startswith('('):
            endargs_idx = tmp_text.find(')', 1)
            if endargs_idx == -1:
                raise Error, '"%s": missing ")"' % self.name
            args_text = tmp_text[1:endargs_idx].strip()
            text = tmp_text[endargs_idx+1:]
            args = [ arg.strip() for arg in args_text.split(',') ]
        return (args, text)

    def parseparms(self, macro_line):
        """Parse macro parameters and store them in self.parms.

        If the macro takes parameters, get their names and verify that they
        are valid names (no invalid characters).  Store them in self.parms.

        Return the text following any parameters.

        """
        (parms, macro_line) = self.getargs(macro_line)
        macro_line = macro_line.lstrip()
        for parm in parms:
            if not self.macro_words.match(parm):
                errstr = '"%s": ' % self.name
                errstr += 'invalid argument: "%s" ' % parm
                errstr += 'valid chars: _, 0-9, a-z, A-Z'
                raise Error, errstr
            self.parms.append(parm)
        return macro_line

    def expandargs(self, args):
        """Expand args into the macro definition."""
        if not self.has_parms():
            return self.definition
        if len(args) != len(self.parms):
            errstr = '"%s": ' % self.name
            errstr += 'expected %d arguments, got %d' % (len(self.parms),
                                                         len(args))
            raise Error, errstr
        low_parms = [ parm.lower() for parm in self.parms ]
        parm2arg = {}
        for i in range(len(low_parms)):
            parm2arg[low_parms[i]] = args[i]
        # Create a copy of the definition to modify.
        definition = self.definition[:]
        # Lowercase the macro definition to simplify searching.
        low_def = definition.lower()
        new_def = ''
        in_word = 0
        while low_def:
            found_parm = 0
            cur_char = definition[0]
            if in_word:
                if cur_char not in self.macro_chars:
                    in_word = 0
            elif cur_char in self.macro_chars:
                for low_parm in low_parms:
                    parm_len = len(low_parm)
                    if (low_def.startswith(low_parm)
                        and (parm_len == len(low_def)
                        or low_def[parm_len] not in self.macro_chars)):
                        # Substitute parameter for the argument.
                        new_def += parm2arg[low_parm]
                        definition = definition[parm_len:]
                        low_def = low_def[parm_len:]
                        found_parm = 1
                        break
                else:
                    in_word = 1
            if not found_parm:
                new_def += cur_char
                definition = definition[1:]
                low_def = low_def[1:]
        return new_def

    def __repr__(self):
        """Print the macro definition.  Useful for debugging."""
        s = 'macro %s' % self.name
        if self.has_parms():
            s += '('
            for i in range(len(self.parms)):
                if i > 0:
                    s += ', '
                s += self.parms[i]
            s += ')'
        s += '\t%s' % self.definition
        return s
    __str__ = __repr__


class _FilterFile:
    """Storage for per-file data.  Used internally by FilterParser."""

    def __init__(self, filename):
        self.lineno = 0
        self.rule_lineno = 0
        self.pushback = None
        self.exception = ParsingError(filename)


class FilterParser:
    bol_comment = re.compile(r'\s*#')

    most_sources = re.compile(r"""
    ( (?:to|from)-(?:file|cdb|dbm|ezmlm|mailman|sql)
    | size | pipe-headers | pipe
    | (?:to|from) (?!-) )
    """, re.VERBOSE | re.IGNORECASE)

    hdrbody_sources = re.compile(r"""
    ( (?:body|headers)-file
    | (?:body|headers) (?!-) )
    """, re.VERBOSE | re.IGNORECASE)

    matches = re.compile(r"""
    (?: ([\'\"]) ( (?: \\\1 | . )+? ) \1
    | ( \S+ ) )
    """, re.VERBOSE)
        
    tag_action = re.compile(r"""
    ( [A-Za-z][-\w]+ ) 
    \s+ 
    (\w+\s*=\s*)?
    (?: 
    ([\'\"]) ( (?: \\\3 | . )+? ) \3
    | ( \S+ ) 
    )
    """, re.VERBOSE)
    
    in_action = re.compile(r"""
    ( drop | exit | stop
    | hold
    | (?: confirm | bounce | reject | deliver | ok | accept)(?:\s*=.*$)? )
    """, re.VERBOSE | re.IGNORECASE)
    
    out_action = re.compile(r"""
    ( (?:(?:bare|sender|domain|dated)(?:=\S+)?)
    | (?:(?:exp(?:licit)?|as|ext(?:ension)?|kw|keyword|shell|python)=\S+)
    | default )""", re.VERBOSE | re.IGNORECASE)
    
    arg_option = re.compile(r'(\w+)(=?)')

    variable = re.compile(r'\$\{([_\w]+)\}')

    arguments = {
        'from'         : None,
        'to'           : None,
        'from-file'    : ('autocdb', 'autodbm', 'optional'),
        'to-file'      : ('autocdb', 'autodbm', 'optional'),
        'from-cdb'     : ('optional',),
        'to-cdb'       : ('optional',),
        'from-dbm'     : ('optional',),
        'to-dbm'       : ('optional',),
        'from-ezmlm'   : ('optional',),
        'to-ezmlm'     : ('optional',),
        'from-mailman' : ('attr', 'optional' ),
        'to-mailman'   : ('attr', 'optional' ),
        'from-sql'     : ('action_column', 'addr_column', 'wildcards'),
        'to-sql'       : ('action_column', 'addr_column', 'wildcards'),
        'body'         : ('case',),
        'headers'      : ('case',),
        'body-file'    : ('case', 'optional'),
        'headers-file' : ('case', 'optional'),
        'size'         : None,
        'pipe-headers' : None,
        'pipe'         : None
        }


    def __init__(self, db_instance=None):
        self.db_instance = db_instance
        self.macros = []
        self.files = []
        self.filterlist = []


    def __pushfile(self, file):
        self.files.append(file)


    def __popfile(self):
        if len(self.files) > 0:
            return self.files.pop()
        return None


    def __file(self):
        if len(self.files) > 0:
            return self.files[-1]
        return None


    def __loadedby(self, filename):
        for idx in range(len(self.files)-1 , -1, -1):
            if filename == self.files[idx].exception.filename:
                if idx > 0:
                    loadername = self.files[idx-1].exception.filename
                else:
                    loadername = sys.argv[0]
                break
        else:
            loadername = None
        return loadername


    def read(self, filename):
        """Open and read the named filter file if it exists."""
        filename = os.path.abspath(filename)
        filename = os.path.normpath(filename)
        loadername = self.__loadedby(filename)

        if loadername:
            errstr = '"%s" already included by "%s"' % (filename, loadername)
            # Get the (still) current file's exception object
            exception = self.__file().exception
            exception.append(self.__file().lineno, errstr)
            raise exception

        try:
            fp = open(filename)
            self.__pushfile(_FilterFile(filename))
            self.__parse(fp)
            fp.close()
            self.__popfile()
        except IOError:
            pass
            

    def __parse(self, fp):
        """
        Parse the filter file.  Comment lines, and blank lines are
        ignored.  Each rule is parsed and, if successful, a tuple
        describing the rule is added to a list (self.filterlist).
        Client code then calls firstmatch, which is where the actual
        matching will take place.

	A ParsingError exception is built up, with detailed error
	messages and, after parsing is completed, the exception is
	raised.
        """
        file = self.__file()

	while 1:
            try:
                rule_line = self.__readrule(fp)
                macro = self.__parsemacro(rule_line)
                if macro:
                    self.macros.append(macro)
                else:
                    rule_line = self.__expandmacros(rule_line, self.macros[:])
                    rule_line = self.__interpolatevars(rule_line)
                    rule_line = self.__includefilter(rule_line)
                    if rule_line:
                        rule = self.__parserule(rule_line)
                        self.filterlist.append(rule)
            except EOFError:
                break
            except ParsingError:
                raise
            except Error, e:
                # A non-fatal parsing error occurred.  Set up the
                # exception but keep going. The exception will be
                # raised at the end of the file and will contain a
                # list of all bogus lines.
                file.exception.append(file.rule_lineno, e._msg)

        # If any parsing errors occurred raise an exception.
        if file.exception.errors:
            raise file.exception


    def __readrule(self, fp):
        rule = None
        file = self.__file()

        while 1:
	    if file.pushback:
		rule = file.pushback
		file.pushback = None
		file.rule_lineno = file.lineno

	    original_line = fp.readline()
	    if not original_line:            # exit loop if out of lines
                if rule:
                    break
	        raise EOFError
	    file.lineno += 1
            # comment at beginning of line, with or without leading whitespace
            if self.bol_comment.match(original_line):
                continue
	    # substitute space characters for tab characters
	    line = string.replace(original_line, '\t', ' ')
            # lose end-of-line comments and trailing whitespace
            line = string.split(line, ' #')[0]
            line = string.rstrip(line)
            # empty line may signify end of current rule
            if line == '':
                if rule:
		    break
                continue
            # may be a line with leading whitespace - a rule continuation
            elif line[0] == ' ':
		if rule:
		    rule = rule + line
		else:
		    # line begins with whitespace, meaning a rule continuation,
                    # but we're not in the middle of a rule.
                    file.rule_lineno = file.lineno
                    raise Error, 'line is improperly indented'
            # line without leading whitespace signifies beginning of new rule
	    #  (and maybe the end of the current rule)
            else:
		if rule:
		    file.pushback = line
		    break
		else:
		    rule = line
		    file.rule_lineno = file.lineno
	return rule


    def __parsemacro(self, rule_line):
        """Parse a macro definition and return a Macro object."""
        macro = None
        if 'macro' == rule_line[:5].lower():
            macro_line = rule_line[5:]
            if not macro_line:
                raise Error, 'incomplete macro definition'
            if macro_line[0] != ' ':
                errstr = '"%s": unrecognized filter rule' % rule_line.split()[0]
                raise Error, errstr
            macro_line = macro_line.lstrip()
            mo = Macro.macro_words.match(macro_line)
            if mo:
                macro = Macro(mo.group(1))
                macro_line = macro_line[mo.end():].lstrip()
                macro.set_definition(macro.parseparms(macro_line))
            else:
                raise Error, 'invalid macro name: valid chars: _, 0-9, a-z, A-Z'
        return macro


    def __expandmacros(self, text, macros):
        """Expand any macros into 'text'.

        Any arguments are expanded into the macro definition.  The expanded
        definition is then recursively expanded to support nested macros.  Once
        the definition is fully expanded, it is inserted into 'text' and 'text'
        is again searched for the current macro.

        This is done for each defined macro.

        """
        for macro in macros:
            rhs = text
            text = ''
            while rhs:
                try:
                    (lhs, rhs) = macro.findname(rhs)
                except ValueError:
                    text += rhs
                    break
                text += lhs
                (args, rhs) = macro.getargs(rhs)
                definition = macro.expandargs(args)
                # Create a copy of the list of macros and remove
                # the current macro to prevent an infinite loop
                # during recursion.
                valid_macros = macros[:]
                valid_macros.remove(macro)
                # Call ourselves to expand any macros in the definition of
                # the current macro.
                definition = self.__expandmacros(definition, valid_macros)
                # Substitute the expanded definition back into the text.
                text += definition
        return text


    def __findvarsub(self, var):
        """Look up 'var' in the Defaults namespace and the environment."""
        # First, check the Defaults namespace.
        sub = Defaults.__dict__.get(var, None)
        # Then, try the environment.
        if not sub:
            sub = os.environ.get(var)
        if not sub:
            raise Error, "${%s} not found in the Defaults " \
                         "namespace nor the environment." % var
        return sub


    def __interpolatevars(self, rule_line):
        """Interpolate variables of the form ${name} into the rule."""
        idx = 0
        while 1:
            mo = self.variable.search(rule_line, idx)
            if not mo:
                break
            var = mo.group(1)
            sub = self.__findvarsub(var)
            rule_line = rule_line[:mo.start()] + sub + rule_line[mo.end():]
        return rule_line


    def __includefilter(self, rule_line):
        optional = 0
        if 'include' == rule_line[:7].lower():
            include_line = rule_line[7:]
            if not include_line:
                raise Error, "incomplete 'include' statement"
            if include_line[0] != ' ':
                errstr = '"%s": unrecognized filter rule' % rule_line.split()[0]
                raise Error, errstr
            include_line = include_line.lstrip()
            if '-optional' == include_line[:9].lower():
                optional = 1
                filename = include_line[9:].lstrip()
            else:
                filename = include_line
            filename = os.path.expanduser(filename)
            if os.path.exists(filename):
                self.read(filename)
            elif not optional:
                raise Error, '"%s": file not found' % filename
            rule_line = None
        return rule_line


    def __parseargs(self, argtuple, rule_line):
        """
        Parse any arguments to the rule.  Arguments begin with a dash
        and must match one of the values in the 'arguments' dictionary.
        """
        match_line = rule_line
        args = {}
        while match_line[:1] == '-':
            # strip off the dash
            match_line = match_line[1:]
            # grab the first word and the optional '='
            mo = self.arg_option.match(match_line)
            if mo:
                # arg is the first word, opt is '=' or None
                (arg, opt) = mo.groups()
                match_line = match_line[mo.end():]
                #if it's not a valid argument, raise an exception
                if not argtuple or arg not in argtuple:
                    raise Error, '"%s": unrecognized argument' % arg
                # grab the option, if there was one
                if opt == '=':
                    mo = self.matches.match(match_line)
                    if mo:
                        opt = mo.group(2) or mo.group(3)
                        match_line = match_line[mo.end():].lstrip()
                    else:
                        raise Error, '"%s" followed by "=" but no option' % arg
                else:
                    match_line = match_line.lstrip()
                args[arg] = opt
            else:
                # whatever followed the '-' wasn't a word!
                raise Error, 'argument contains garbage characters'
        return args, match_line


    def __parserule(self, rule_line):
	"""
	Parse a single rule from a filter file.  If successful, return a tuple
	with five fields.  The five fields are:
	
	  source    - string: to*, from*, body*, headers*, size, pipe, pipe-headers
          args      - any arguments that might be specified
	  match     - string: the email address to be matched against, a
                      filename or a regular expression enclosed within
                      parentheses
	  actions   - dictionary: a dictionary with a key of 'action' and
                      a value that is a tuple.

                      Incoming actions have key 'incoming' and the tuple
                      contains the action and an optional parameter.

                        { 'incoming' : ( 'deliver', '&tim@catseye.net' ) }

                      Outgoing actions have the relevant header as the key and
                      the tuple contains the 'cookie' type and the 'cookie'
                      option.

                        { 'from' : ( 'exp', 'tim@catseye.net' ) }

                      In the case of the outgoing filter, the dictionary may have
                      more than one entry. In fact, that's the reason we use a
                      dictionary. The rather silly looking incoming entry is a
                      usable, but unfortunate consequence of providing a useful
                      data structure for tmda-inject.
          lineno    - integer: The line number the rule began on.
	"""
	rule = None
	# first, get the source and the match
	mo = self.most_sources.match(rule_line)
        if not mo:
            mo = self.hdrbody_sources.match(rule_line)
	if not mo:
	    raise Error, '"%s": unrecognized filter rule' % rule_line.split()[0]
	else:
	    source = mo.group(1)
            match_line = string.lstrip(rule_line[mo.end():])
            args, match_line = self.__parseargs(self.arguments[source.lower()],
                                                match_line)
            mo = self.matches.match(match_line)
            if not mo:
                # missing match
                raise Error, '"%s": missing <match> field' % source
            else:
                match = mo.group(2) or mo.group(3)
                action_line = string.lstrip(match_line[mo.end():])
                actions = self.__buildactions(action_line, source)
                rule = (source, args, match, actions, self.__file().rule_lineno)
	return rule


    def __buildactions(self, action_line, source):
	"""
	Build and return a dictionary of actions. The dictionary structure is
        described in the documentation for the __parserule function.
	"""
	actions = None
	if action_line[:len('tag ')] == 'tag ':
	    action_line = string.lstrip(action_line[len('tag '):])
	    while len(action_line) > 0:
		mo = self.tag_action.match(action_line)
                if not mo:
                    # must not be two fields
                    errstr = '"%s": ' % source
                    errstr += 'malformed header field or missing <action>'
                    raise Error, errstr
                header = string.lower(mo.group(1))
                action = (mo.group(2) or "") + (mo.group(4) or mo.group(5))
                if action:
                    if not actions:
                        actions = {}
                    if self.out_action.match(action):
                        actions[header] = splitaction(action)
                    else:
                        actions[header] = (None, action)
		else:
		    # don't know how we could get here
		    raise Error, 'unexpected error'
		action_line = string.lstrip(action_line[mo.end()+1:])
	else:
	    mo = self.in_action.match(action_line)
	    if mo:
		if len(action_line) == len(mo.group(1)):
                    actions = { 'incoming' : splitaction(action_line) }
		else:
		    # invalid incoming action (extra stuff on line)
		    raise Error, '"%s": garbage at end of line' % source
	    else:
		mo = self.out_action.match(action_line)
		if mo:
		    if len(action_line) == len(mo.group(1)):
                        actions = { 'from' : splitaction(action_line) }
		    else:
			# invalid outgoing action (extra stuff on line)
                        raise Error, '"%s": garbage at end of line' % source
                else:
                    # missing action!
                    errstr = '"%s": missing or bogus <action> field' % source
                    raise Error, errstr
	return actions
	

    def __search_list(self, addrlist, keys, actions, source):
        """Search addrlist for match in field 1, optional action in 2."""
        # This list comprehension splits each line in the list into
        # two columns, lowercases the first column and stuffs the
        # columns back together.  The result is the original list of
        # lines from the file with the first field in each line
        # lowercased.
        addrlist = [' '.join(
            apply(lambda f1, f2=None: f2 and [f1.lower(), f2]
                                          or [f1.lower()],
                  line.split(None, 1))) for line in addrlist]
        found_match = Util.findmatch(addrlist, keys)
        if found_match:
            # The second column of the line may contain an
            # overriding action specification.
            if found_match != 1:
                actions.clear()
                actions.update(self.__buildactions(found_match, source))
                # it's already true, but everywhere else it's 1
                found_match = 1
        return found_match


    def __search_file(self, pathname, keys, actions, source):
        """
        Search a text file for match in first column.
        """
        return self.__search_list(Util.file_to_list(pathname),
                                  keys,
                                  actions,
                                  source)


    def __search_cdb(self, pathname, keys, actions, source):
        """
        Search DJB's constant databases; see <http:/cr.yp.to/cdb.html>.
        """
        import cdb
        cdb = cdb.init(pathname)
        found_match = 0
        for key in keys:
            if key and cdb.has_key(string.lower(key)):
                found_match = 1
                cdb_value = cdb[string.lower(key)]
                # If there is an entry for this key,
                # we consider it an overriding action
                # specification.
                if cdb_value:
                    actions.clear()
                    actions.update(self.__buildactions(cdb_value, source))
                break
        return found_match


    def __search_dbm(self, pathname, keys, actions, source):
        """
        Search a DBM-style database.
        """
        import anydbm
        dbm = anydbm.open(pathname, 'r')
        found_match = 0
        for key in keys:
            if key and dbm.has_key(string.lower(key)):
                found_match = 1
                dbm_value = dbm[string.lower(key)]
                # If there is an entry for this key,
                # we consider it an overriding action
                # specification.
                if dbm_value:
                    actions.clear()
                    actions.update(self.__buildactions(dbm_value, source))
                dbm.close()
                break
        return found_match


    def __autobuild_db(self, basename, extension,
                       surrogate, build_func, search_func, optional):
        """
        Automatically build a CDB/DBM database if it's out-of-date.
        """
        dbname = basename + extension
        try:
            txt_mtime = os.path.getmtime(basename)
        except OSError:
            # If the text file doesn't exist, and the optional flag is not
            # specified, re-raise the exception.
            if optional:
                search_func = None
            else:
                raise
        else:
            # If the db doesn't exist, that's not an error.
            try:
                db_mtime = os.path.getmtime(surrogate)
            except OSError:
                db_mtime = 0
            if db_mtime <= txt_mtime:
                if build_func(basename):
                    if os.path.exists(surrogate):
                        os.utime(surrogate, None)
                    else:
                        os.close(os.open(surrogate, os.O_CREAT, 0600))
                else:
                    dbname = basename
                    search_func = self.__search_file
        return (dbname, search_func)


    def __extract_domains(self, keys):
        """
        Attempt to extract the domain name from each address in keys.
        """
        domains = {}
        for k in keys:
            try:
                domains[k.split('@', 1)[1]] = None
            except IndexError:
                pass
        return domains.keys()


    def __create_sql_criteria(self, dbkeys, addresscolumn):
        """Return condition string for insertion into SQL statement."""
        if not dbkeys:
            return ''
        criteria = "("
        for i in range(len(dbkeys)):
            if i > 0:
                criteria += " OR "
            criteria += "%s = %%(criterion%d)s" % (addresscolumn, i)
        criteria += ")"
        return criteria


    def __get_column_index(self, colname, cursor):
        """Return index of column named 'colname'."""
        for i in range(len(cursor.description)):
            if colname == cursor.description[i][0]:
                return i
        return -1


    def __search_sql(self, selectstmt, args, keys, actions, source, lineno):
        """Search SQL DB (Python DB API 2.0)."""
        found_match = 0
        dbkeys = keys
        if args.has_key('wildcards'):
            dbkeys = []
        _username = Defaults.USERNAME.lower()
        _hostname = Defaults.HOSTNAME.lower()
        _recipient = _username + '@' + _hostname
        params = create_sql_params(dbkeys,
                                   recipient=_recipient,
                                   username=_username,
                                   hostname=_hostname)
        cursor = self.db_instance.cursor()
        try:
            cursor.execute(selectstmt, params)
            rows = cursor.fetchall()
            if cursor.rowcount <= 0:
                return 0
            if args.has_key('wildcards'):
                if len(cursor.description) > 1:
                    dblist = [' '.join([row[0], row[1] or '']) for row in rows]
                else:
                    dblist = [row[0] for row in rows]
                found_match = self.__search_list(dblist, keys, actions, source)
            else:
                action_column = args.get('action_column')
                if action_column:
                    actcolidx = self.__get_column_index(action_column, cursor)
                    if actcolidx == -1:
                        actcolidx = self.__get_column_index(
                            action_column.lower(), cursor)
                        if actcolidx == -1:
                            err = "no action column (%s)" % (action_column,)
                            raise MatchError(lineno, err)
                    action = rows[0][actcolidx]
                    if action:
                        actions.clear()
                        actions.update(self.__buildactions(action, source))
                found_match = 1
        finally:
            cursor.close()
        return found_match


    def firstmatch(self, recipient, senders=None,
                   msg_body=None, msg_headers=None, msg_size=None):
        """Iterate over each rule in the list looking for a match.  As
        soon as a match is found exit, returning the corresponding
        action dictionary and matching line.
        """
        line = None
	found_match = None
        for (source, args, match, actions, lineno) in self.filterlist:
            source = string.lower(source)
            # set up the keys for searching
            if source.startswith('from') and senders:
                keys = senders
            elif source.startswith('to') and recipient:
                keys = [recipient]
            # Here starts the matching against the various rules
            #
            # regular 'from' or 'to' addresses
            if source in ('from', 'to'):
                found_match = Util.findmatch([string.lower(match)], keys)
		if found_match:
		    break
            # 'from-file' or 'to-file', including autocdb functionality
            if source in ('from-file', 'to-file'):
                dbname = os.path.expanduser(match)
                search_func = self.__search_file
                keys += self.__extract_domains(keys)
                # If we have an 'auto*' argument, ensure that the database
                # is up-to-date.  If the 'optional' argument is also given,
                # don't die if the file doesn't exist.
                optional = args.has_key('optional')
                if args.has_key('autocdb'):
                    (dbname, search_func) = self.__autobuild_db(
                        dbname, '.cdb', dbname + '.cdb',
                        Util.build_cdb, self.__search_cdb, optional)
                elif args.has_key('autodbm'):
                    (dbname, search_func) = self.__autobuild_db(
                        dbname, '.db', dbname + '.last_built',
                        Util.build_dbm, self.__search_dbm, optional)
                else:
                    if not os.path.exists(dbname) and optional:
                        search_func = None
                try:
                    if search_func:
                        found_match = search_func(dbname, keys,
                                                  actions, source)
                except Error, e:
                    raise MatchError(lineno, e._msg)
                if found_match:
                    break
            # DBM-style databases.
            if source in ('from-dbm', 'to-dbm'):
                import anydbm
                match = os.path.expanduser(match)
                keys += self.__extract_domains(keys)
                try:
                    found_match = self.__search_dbm(match, keys,
                                                    actions, source)
                except anydbm.error, e:
                    if not args.has_key('optional'):
                        raise MatchError(lineno, str(e))
                if found_match:
		    break
            # DJB's constant databases; see <http://cr.yp.to/cdb.html>.
            if source in ('from-cdb', 'to-cdb'):
                import cdb
                match = os.path.expanduser(match)
                keys += self.__extract_domains(keys)
                try:
                    found_match = self.__search_cdb(match, keys,
                                                    actions, source)
                except cdb.error, e:
                    if not args.has_key('optional'):
                        raise MatchError(lineno, str(e))
                if found_match:
                    break
            # ezmlm subscriber directories.
            if source in ('from-ezmlm', 'to-ezmlm'):
                match = os.path.join(os.path.expanduser(match), 'subscribers')
                ezmlm_list = []
                try:
                    # See ezmlm(5) for dir/subscribers format.
                    for file in os.listdir(match):
                        fp = open(os.path.join(match, file), 'r')
                        subs = fp.read().split('\x00')
                        for sub in subs:
                            if sub:
                                ezmlm_list.append(sub.split('T', 1)[1].lower())
                    for key in keys:
                        if key and key.lower() in ezmlm_list:
                            found_match = 1
                            break
                except OSError:
                    if not args.has_key('optional'):
                        raise
                if found_match:
                    break
            # Mailman configuration databases.
            if source in ('from-mailman', 'to-mailman'):
                match = os.path.expanduser(match)
                try:
                    mmdb_key = args['attr']
                except KeyError:
                    raise MatchError(lineno,
                                     '"%s" missing -attr argument' % source)
                # Find the Mailman configuration database.
                # 'config.db' is a Python marshal used in MM 2.0, and
                # 'config.pck' is a Python pickle used in MM 2.1.
                try_open = 1  # Try to open file.
                config_db = os.path.join(match, 'config.db')
                config_pck = os.path.join(match, 'config.pck')
                if os.path.exists(config_pck):
                    dbfile = config_pck
                    import cPickle as Serializer
                elif os.path.exists(config_db):
                    dbfile = config_db
                    import marshal as Serializer
                elif args.has_key('optional'):
                    # This is the case where neither of the Mailman
                    # configuration databases exists.  If the -optional flag
                    # was specified, don't bother trying to open a non-existent
                    # file.
                    try_open = 0
                if try_open:
                    mmdb_file = open(dbfile, 'r')
                    mmdb_data = Serializer.load(mmdb_file)
                    mmdb_file.close()
                    mmdb_addylist = mmdb_data[mmdb_key]
                    # Make sure mmdb_addylist is a list of e-mail addresses.
                    if type(mmdb_addylist) is types.DictType:
                         mmdb_addylist = mmdb_data[mmdb_key].keys()
                    for addy in keys:
                        if addy and addy.lower() in mmdb_addylist:
                            found_match = 1
                            break
                if found_match:
		    break
            # Generic SQL.  Expects a SELECT statement as the 'match' field.
            # There are two "modes", depending on the presence of TMDA-style
            # wildcards in the database.  See the filter source documentation
            # for more information.
            if source in ('from-sql', 'to-sql'):
                selectstmt = match
                keys += self.__extract_domains(keys)
                addr_column = args.get('addr_column')
                if args.has_key('wildcards'):
                    if addr_column:
                        raise MatchError(lineno,
                                         "-addr_column and -wildcards " +
                                         "cannot be used together")
                elif not addr_column:
                    raise MatchError(lineno, "-addr_column must be specified")
                else:
                    criteria = self.__create_sql_criteria(keys, addr_column)
                    selectstmt = selectstmt.replace('%(criteria)s', criteria)
                found_match = self.__search_sql(
                    selectstmt, args, keys, actions, source, lineno)
                if found_match:
                    break
            # A match is found if the command exits with a zero exit
            # status.
            if source == 'pipe-headers' and msg_headers:
                cmd = popen2.Popen3(match, 1, bufsize=-1)
                cmdout, cmdin, cmderr = cmd.fromchild, cmd.tochild, cmd.childerr
                cmdin.write(msg_headers)
                cmdin.flush()
                cmdin.close()
                err = cmderr.read().strip()
                cmderr.close()
                out = cmdout.read().strip()
                cmdout.close()
                r = cmd.wait()
                if r == 0:
                    found_match = 1
                    break
                else:
                    # non-zero exit status
                    if os.WIFEXITED(r):
                        pass
                    # raise an exception if the process exited due to
                    # a signal.
                    elif os.WIFSIGNALED(r):
                        raise Error, 'command "%s" abnormal exit signal %s (%s)' \
                              % (match, os.WTERMSIG(r), err or '')
            # A match is found if the command exits with a zero exit
            # status.
            if source == 'pipe' and msg_body and msg_headers:
                cmd = popen2.Popen3(match, 1, bufsize=-1)
                cmdout, cmdin, cmderr = cmd.fromchild, cmd.tochild, cmd.childerr
                cmdin.write(msg_headers + '\n' + msg_body)
                cmdin.flush()
                cmdin.close()
                err = cmderr.read().strip()
                cmderr.close()
                out = cmdout.read().strip()
                cmdout.close()
                r = cmd.wait()
                if r == 0:
                    found_match = 1
                    break
                else:
                    # non-zero exit status
                    if os.WIFEXITED(r):
                        pass
                    # raise an exception if the process exited due to
                    # a signal.
                    elif os.WIFSIGNALED(r):
                        raise Error, 'command "%s" abnormal exit signal %s (%s)' \
                              % (match, os.WTERMSIG(r), err or '')
            if source in ('body', 'headers'):
                if source == 'body' and msg_body:
                    content = msg_body
                elif source == 'headers' and msg_headers:
                    content = msg_headers
                else:
                    content = None
                re_flags = re.MULTILINE
                if not args.has_key('case'):
                    re_flags = re_flags | re.IGNORECASE
                if content and re.search(match,content,re_flags):
		    found_match = 1
                    break
            if source in ('body-file','headers-file'):
                match = os.path.expanduser(match)
                try:
                    match_list = Util.file_to_list(match)
                except IOError:
                    if not args.has_key('optional'):
                        raise
                else:
                    if source == 'body-file' and msg_body:
                        content = msg_body
                    elif source == 'headers-file' and msg_headers:
                        content = msg_headers
                    else:
                        content = None
                    re_flags = re.MULTILINE
                    if not args.has_key('case'):
                        re_flags = re_flags | re.IGNORECASE
                    for line in match_list:
                        mo = self.matches.match(line)
                        if mo:
                            expr = mo.group(2) or mo.group(3)
                            if content and re.search(expr,content,re_flags):
                                found_match = 1
                                break
                if found_match:
		    break
            if source == 'size' and msg_size:
                match_list = list(match)
                operator = match_list[0] # first character should be < or >
                bytes = string.join(match_list,'')[1:] # rest is the size
                found_match = None
                if operator == '<':
                    found_match = int(msg_size) < int(bytes)
                elif operator == '>':
                    found_match = int(msg_size) > int(bytes)
                if found_match:
                    break
	if found_match:
	    line = _rulestr(source, args, match, actions)
	else:
	    actions = {}
	return actions, line


def _rulestr(source, args, match, actions):
    """
    Build string from source, args, match and actions.
    """
    if source in ('headers', 'body'):
        match = '"' + str(match) + '"'
    argstr = _argstr(args)
    line = str(source) + ' '
    if argstr:
        line += argstr + ' '
    line += match + ' ' + _actionstr(actions)
    return line


def _argstr(args):
    """
    Build argument string from args dictionary
    """
    return ' '.join([ '-' + _cookiestr(item) for item in args.items() ])


def _actionstr(actions):
    """
    Build string from action dictionary.
    """
    line = ''
    if actions:
	for header, (action, option) in actions.items():
            mo = FilterParser.in_action.match(action or '')
	    if mo:
		line = line + action
	    else:
                if len(line) == 0:
                    line = line + 'tag'
		line = line + ' ' + header
                if action:
                    line = line + ' ' + _cookiestr((action, option))
		else:
		    line = line + ' "' + str(option) + '"'
    return line


def _cookiestr(action):
    argstr = str(action[0])
    argvalue = action[1]
    if argvalue:
        if ' ' in argvalue:
            argvalue = '"%s"' % argvalue
	argstr += '=' + str(argvalue)
    return argstr


def splitaction(action):
    """
    Split the action at the '=' and return a tuple of the two
    parts. If there is no '=', the second field in the tuple will
    be None.
    """
    # Split the action=option apart if possible.
    parts = [ part.strip() for part in action.split('=', 1) ]
    if len(parts) == 1:
        return (parts[0], None)
    return tuple(parts)


def create_sql_params(dbkeys=[], **kwargs):
    """Return dictionary of parameters for SQL statement."""
    params = kwargs.copy()
    for i in range(len(dbkeys)):
        params['criterion'+str(i)] = dbkeys[i]
    return params

