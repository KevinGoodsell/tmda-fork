# -*- python -*-

"""
TMDA filter file parser.

Filter file syntax documented in htdocs/config-filter.html
"""


import os
import re
import string
import types

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


class FilterParser:
    bol_comment = re.compile(r'\s*#')

    most_sources = re.compile(r"""
    ( (?:to|from)-(?:file|cdb|dbm|ezmlm|mailman)
    | size
    | (?:to|from) (?!-) )
    """, re.VERBOSE | re.IGNORECASE)

    hdrbody_sources = re.compile(r"""
    ( (?:body|headers)-file
    | (?:body|headers) (?!-) )
    """, re.VERBOSE | re.IGNORECASE)

    matches = re.compile(r"""
    (?: ([\'\"]) ( (?: \\\1 | [^\1] )+ ) \1
    | ( \S+ ) )
    """, re.VERBOSE)
        
    tag_action = re.compile(r"""
    ( [A-Za-z][-\w]+ )
    \s+
    (?: ([\'\"]) ( (?: \\\2 | [^\2] )+ ) \2
    | ( \S+ ) )
    """, re.VERBOSE)

    in_action = re.compile(r"""
    (bounce|reject|drop|exit|stop|ok|accept|confirm
    | deliver(?:\s*=.*$)? )
    """, re.VERBOSE | re.IGNORECASE)
    
    out_action = re.compile(r"""
    ( (?:(?:bare|sender|dated)(?:=\S+)?)
    | (?:(?:exp(?:licit)?|as|ext(?:ension)?|kw|keyword)=\S+)
    | default )""", re.VERBOSE | re.IGNORECASE)
    
    action_option = re.compile(r'(\w+)(?:\s*=\s*(.*)$)?')

    arg_option = re.compile(r'(\w+)(=?)')

    arguments = {
        'from'         : None,
        'to'           : None,
        'from-file'    : ('autocdb',),
        'to-file'      : ('autocdb',),
        'from-cdb'     : None,
        'to-cdb'       : None,
        'from-dbm'     : None,
        'to-dbm'       : None,
        'from-ezmlm'   : None,
        'to-ezmlm'     : None,
        'from-mailman' : ('attr',),
        'to-mailman'   : ('attr',),
        'body'         : ('case',),
        'headers'      : ('case',),
        'body-file'    : ('case',),
        'headers-file' : ('case',),
        'size'         : None
        }


    def __init__(self):
        pass


    def read(self, filename):
        """Open and read the named filter file if it exists."""
        self.filename = filename
        self.filterlist = []
        self.__lineno = 0
        self.__rule_lineno = 0
        self.__pushback = None

        if os.path.exists(filename):
            fp = open(filename)
            self.__parse(fp)
            fp.close()
            

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
        exception = ParsingError(self.filename)

	while 1:
            try:
                rule_line = self.__readrule(fp)
                rule = self.__parserule(rule_line)
		self.filterlist.append(rule)
            except EOFError:
                break
            except Error, e:
                # A non-fatal parsing error occurred.  Set up the
                # exception but keep going. The exception will be
                # raised at the end of the file and will contain a
                # list of all bogus lines.
                exception.append(self.__rule_lineno, e._msg)

        # If any parsing errors occurred raise an exception.
        if exception.errors:
            raise exception


    def __readrule(self, fp):
        rule = None

        while 1:
	    if self.__pushback:
		rule = self.__pushback
		self.__pushback = None
		self.__rule_lineno = self.__lineno

	    original_line = fp.readline()
	    if not original_line:            # exit loop if out of lines
                if rule:
                    break
	        raise EOFError
	    self.__lineno = self.__lineno + 1
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
                    self.__rule_lineno = self.__lineno
                    raise Error, 'line is improperly indented'
            # line without leading whitespace signifies beginning of new rule
	    #  (and maybe the end of the current rule)
            else:
		if rule:
		    self.__pushback = line
		    break
		else:
		    rule = line
		    self.__rule_lineno = self.__lineno
	return rule


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
	
	  source    - string: to*, from*, body*, headers*, size
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
                rule = (source, args, match, actions, self.__rule_lineno)
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
		action = mo.group(3) or mo.group(4)
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
	

    def __search_file(self, pathname, keys, actions, source):
        """
        Search a text file for match in first column.
        """
        found_match = 0
        match_list = Util.file_to_list(pathname)
        # This list comprehension splits each line in the list into
        # two columns, lowercases the first column and stuffs the
        # columns back together.  The result is the original list of
        # lines from the file with the first field in each line
        # lowercased.
        match_list = [' '.join(
            apply(lambda f1, f2=None: f2 and [f1.lower(), f2]
                                          or [f1.lower()],
                  line.split(None, 1))) for line in match_list]
        found_match = Util.findmatch(match_list, keys)
        if found_match:
            # The second column of the line may contain an
            # overriding action specification.
            if found_match != 1:
                actions.clear()
                actions.update(self.__buildactions(found_match, source))
                # it's already true, but everywhere else it's 1
                found_match = 1
        return found_match


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
            #
            # Here starts the matching against the various rules
            #
            # regular 'from' or 'to' addresses
            if source in ('from', 'to'):
                found_match = Util.findmatch([string.lower(match)], keys)
		if found_match:
		    break
            # 'from-file' or 'to-file', including autocdb functionality
            if source in ('from-file', 'to-file'):
                match = os.path.expanduser(match)
                valid_cdb = 0
                if args.has_key('autocdb'):
                    cdbname = match + '.cdb'
                    # If the text file doesn't exist, let the exception
                    #  happen and get passed back to tmda-filter.
                    txtmtime = os.path.getmtime(match)
                    # If the cdb file doesn't exist, that's not an error.
                    try:
                        cdbmtime = os.path.getmtime(cdbname)
                    except OSError:
                        cdbmtime = 0
                    valid_cdb = 1
                    if cdbmtime <= txtmtime:
                        valid_cdb = Util.build_cdb(match)
                # At this point, valid_cdb will be 1 (true) if there
                # is an -autocdb flag and the .cdb is now up-to-date.
                # If there was no -autocdb flag or if there was an
                # error rebuilding an autocdb, valid_cdb be 0 (false).
                try:
                    if valid_cdb:
                        found_match = self.__search_cdb(cdbname, keys,
                                                        actions, source)
                    else:
                        found_match = self.__search_file(match, keys,
                                                         actions, source)
                except Error, e:
                    raise MatchError(lineno, e._msg)
                if found_match:
                    break
            # DBM-style databases.
            if source in ('from-dbm', 'to-dbm'):
                match = os.path.expanduser(match)
                import anydbm
                dbm = anydbm.open(match,'r')
                for key in keys:
                    if key and dbm.has_key(string.lower(key)):
			found_match = 1
                        dbm_value = dbm[string.lower(key)]
                        # If there is an entry for this key,
                        # we consider it an overriding action
                        # specification.
                        if dbm_value:
                            actions = self.__buildactions(dbm_value, source)
                        dbm.close()
                        break
                if found_match:
		    break
            # DJB's constant databases; see <http://cr.yp.to/cdb.html>.
            if source in ('from-cdb', 'to-cdb'):
                match = os.path.expanduser(match)
                try:
                    found_match = self.__search_cdb(match, keys,
                                                    actions, source)
                except Error, e:
                    raise MatchError(lineno, e._msg)
                if found_match:
                    break
            # ezmlm `subscribers' directories.
            if source in ('from-ezmlm', 'to-ezmlm'):
                match = os.path.expanduser(match)
                ezmlm_list = []
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
                if found_match:
                    break
            # Mailman list-configuration databases.
            if source in ('from-mailman', 'to-mailman'):
                match = os.path.expanduser(match)
                try:
                    mmdb_key = args['attr']
                except KeyError:
                    raise MatchError(lineno,
                                     '"%s" missing -attr argument' % source)
                # The filename is expected to be in the format of
                # either 'filename.db', or 'filename.pck'.
                dbsuffix = string.split(match, '.')[-1]
                # If the filename ends with `.db', then it is
                # assumed that the file contains a Python marshal
                # (MM 2.0).  If the file ends with `.pck' then it
                # is assumed to contain a Python pickle (MM 2.1).
                if dbsuffix == 'db':
                    import marshal
                    Serializer = marshal
                elif dbsuffix == 'pck':
                    import cPickle
                    Serializer = cPickle
                mmdb_file = open(match, 'r')
                mmdb_data = Serializer.load(mmdb_file)
                mmdb_file.close()
                mmdb_addylist = mmdb_data[mmdb_key]
                # Make sure mmdb_addylist is a list of e-mail addresses.
                if type(mmdb_addylist) is types.DictType:
                     mmdb_addylist = mmdb_data[mmdb_key].keys()
                for addy in keys:
                    if addy and string.lower(addy) in mmdb_addylist:
                        found_match = 1
                        break
                if found_match:
		    break
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
                match_list = Util.file_to_list(match)
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
	    actions = None
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
	for header, action in actions.items():
	    mo = FilterParser.in_action.match(header)
	    if mo:
		line = line + header
	    else:
                if len(line) == 0:
                    line = line + 'tag'
		line = line + ' '+ header
                if action[0]:
                    line = line + ' ' + _cookiestr(action)
		else:
		    line = line + ' "' + str(action[1]) + '"'
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
    be None. If the first part of the action cannot be matched,
    the returned tuple will be (None, None).
    """
    # Split the action=option apart if possible.
    mo = FilterParser.action_option.match(action)
    if mo:
        return string.lower(mo.group(1)), mo.group(2)
    return None, None
