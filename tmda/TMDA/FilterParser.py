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
    def __repr__(self):
        return self._msg
    __str__ = __repr__

class ParsingError(Error):
    """Exception raised on parsing errors in the filter file."""
    def __init__(self, filename):
        Error.__init__(self, 'Filter contains parsing errors: %s' % filename)
        self.filename = filename
        self.errors = []

    def append(self, lineno, line):
        self.errors.append((lineno, line))
        self._msg = self._msg + '\n\t[line %2d]: %s' % (lineno, line)


class FilterParser:
    bol_comment = re.compile(r'\s*#')

    most_sources = re.compile(r"""
    ( (?:(?:to|from)(?:-(?:file|cdb|dbm|autocdb|autodbm|ezmlm|mailman\.\S+))?)
    | size )
    \ (?# NOTE: preceding character must be an actual space)
    """, re.VERBOSE | re.IGNORECASE)

    hdrbody_sources = re.compile(r"""
    ( (?:body|headers)(?:-file)?)
    \ (?# NOTE: preceding character must be an actual space)
    """, re.VERBOSE | re.IGNORECASE)

    matches = re.compile(r"""
    (?: ([\'\"]) ( (?: \\\1 | [^\1] )+ ) \1
    | ( \S+ ) )
    """, re.VERBOSE)
        
    tag_action = re.compile(r'([A-Za-z][-\w]+)\s+(\S+)')

    in_action = re.compile(r'(bounce|reject|drop|exit|stop|ok|accept|deliver|confirm)',
                           re.IGNORECASE)
    
    out_action = re.compile(r"""
    ( (?:(?:bare|sender|dated)(?:=\S+)?)
    | (?:(?:exp(?:licit)?|as|ext(?:ension)?|kw|keyword)=\S+)
    | default )""", re.VERBOSE | re.IGNORECASE)
    
    action_option = re.compile(r'(\w+)(?:=(\S+))?')


    def __init__(self, checking=None):
        self.checking = checking
        

    def read(self, filename):
        """Open and read the named filter file.  Files that cannot be opened
        are silently ignored."""
	self.filename = filename
        self.filterlist = []
	self.__lineno = 0
	self.__rule_lineno = 0
	self.__pushback = None
        self.__exception = None

        if os.path.exists(filename):
            try:
                fp = open(filename)
                self.__parse(fp)
                fp.close()
            except IOError:
                pass


    def __parse(self, fp):
        """
        Parse the filter file.  Comment lines, blank lines, and lines
        with invalid syntax are ignored.  Each rule is parsed and, if
	successful, a tuple describing the rule is added to a list
	(self.filterlist) which is where the actual matching will
        take place.  [See __parserule()]

	Errors are silently ignored unless self.checking is true.  If
	self.checking is true, a ParsingError exception is built up,
	with detailed error messages and, after parsing is completed,
	the exception is raised.
        """
	while 1:
	    rule_line = self.__readrule(fp)
	    if not rule_line:
		break
	    rule = self.__parserule(rule_line)
	    if rule:
		self.filterlist.append(rule)

        # If any parsing errors occurred and we are running in check
        # mode, raise an exception.
        if self.__exception:
            raise self.__exception


    def __readrule(self, fp):
        rule = None

        while 1:
	    if self.__pushback:
		rule = self.__pushback
		self.__pushback = None
		self.__rule_lineno = self.__lineno

	    original_line = fp.readline()
	    if not original_line:            # exit loop if out of lines
	        break
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
		    # add to ParseError exception
		    self.__adderror(self.__lineno, original_line)
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


    def __parserule(self, rule_line):
	"""
	Parse a single rule from a filter file.  If successful, return a tuple
	with three fields.  The three fields are:
	
	  source    - string: to*, from*, body, headers, size, default
	  match     - string: the email address to be matched against, a
                      filename or a regular expression enclosed within
                      parentheses
	  actions   - dictionary: a dictionary with a key of 'action' and
                      a value that is a tuple. The value tuple contains
                      the 'cookie' type and the 'cookie' option. Ex:
                        { 'accept' : ( None, None ) }           # incoming
                        { 'from' : ( 'exp', 'tim@catseye.net' ) # outgoing
                      In the case of the outgoing filter, the dictionary may have
                      more than one entry. In fact, that's the reason we use a
                      dictionary. The rather silly looking incoming entry is a
                      usable, but unfortunate consequence of providing a useful
                      data structure for tmda-inject.
	"""
	rule = None
	# first, get the source and the match
	mo = self.most_sources.match(rule_line)
        if not mo:
            mo = self.hdrbody_sources.match(rule_line)
	if not mo:
	    self.__adderror(self.__rule_lineno, rule_line)
	else:
	    source = mo.group(1)
            match_line = string.lstrip(rule_line[mo.end():])
            mo = self.matches.match(match_line)
            if not mo:
                # missing match
                self.__adderror(self.__rule_lineno, match_line)
            else:
                match = mo.group(2) or mo.group(3)
                action_line = string.lstrip(match_line[mo.end():])
                actions = self.__buildactions(action_line, rule_line)
                if actions:
                    rule = (source, match, actions)
                else:
                    # missing action!
                    self.__adderror(self.__rule_lineno, action_line)
	return rule


    def __adderror(self, lineno, line, error=''):
        """
        Create a new exception object if necessary and append the latest
        error to it. This only takes place if self.checking is true.
        """
	# A non-fatal parsing error occurred.  Set up the
	# exception but keep going. The exception will be
	# raised at the end of the file and will contain a
	# list of all bogus lines.
	if self.checking:
	    if not self.__exception:
		self.__exception = ParsingError(self.filename)
	    self.__exception.append(lineno, `line`)


    def __buildactions(self, action_line, rule_line=None):
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
                    self.__adderror(self.__rule_lineno, rule_line)
		    break
		header = string.lower(mo.group(1))
		action = mo.group(2)
		if self.out_action.match(action):
                    if not actions:
                        actions = {}
		    actions[header] = splitaction(action)
		else:
		    # malformed action
		    self.__adderror(self.__rule_lineno, action)
		action_line = string.lstrip(action_line[mo.end()+1:])
	else:
	    mo = self.in_action.match(action_line)
	    if mo:
		if len(action_line) == len(mo.group(1)):
                    actions = { action_line.lower() : (None, None) }
		else:
		    # invalid incoming action (extra stuff on line)
		    self.__adderror(self.__rule_lineno, rule_line)
	    else:
		mo = self.out_action.match(action_line)
		if mo:
		    if len(action_line) == len(mo.group(1)):
                        actions = { 'from' : splitaction(action_line) }
		    else:
			# invalid outgoing action
			self.__adderror(self.__rule_lineno, rule_line)
	return actions
	

    def __search_file(self, pathname, keys, actions):
        found_match = 0
        match_list = []
        match_list = Util.file_to_list(pathname, match_list)
        found_match = Util.findmatch(match_list, keys)
        if found_match:
            # The second column of the line may contain an
            # overriding action specification.
            if found_match != 1:
                actions.clear()
                actions.update(self.__buildactions(found_match))
                # it's already true, but everywhere else it's 1
                found_match = 1
        return found_match


    def __search_cdb(self, pathname, keys, actions):
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
                    actions.update(self.__buildactions(cdb_value))
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
        for (source, match, actions) in self.filterlist:
            source = string.lower(source)
            if source in ('from', 'to'):
                if source == 'from' and senders:
		    found_match = Util.findmatch([string.lower(match)],
                                                 senders)
                elif source == 'to' and recipient:
		    found_match = Util.findmatch([string.lower(match)],
                                                 [recipient])
		if found_match:
		    break
            if source in ('from-file', 'to-file'):
                match = os.path.expanduser(match)
                if source == 'from-file' and senders:
                    keys = senders
                elif source == 'to-file' and recipient:
                    keys = [recipient]
                found_match = self.__search_file(match, keys, actions)
                if found_match:
                    break
            # DBM-style databases.
            if source in ('from-dbm', 'to-dbm'):
                match = os.path.expanduser(match)
                if source == 'from-dbm':
                    keys = senders
                elif source == 'to-dbm':
                    keys = [recipient]
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
                            actions = self.__buildactions(dbm_value)
                        dbm.close()
                        break
                if found_match:
		    break
            # DJB's constant databases; see <http://cr.yp.to/cdb.html>.
            if source in ('from-cdb', 'to-cdb'):
                match = os.path.expanduser(match)
                if source == 'from-cdb' and senders:
                    keys = senders
                elif source == 'to-cdb' and recipient:
                    keys = [recipient]
                found_match = self.__search_cdb(match, keys, actions)
                if found_match:
                    break
            # auto-build DJB's constant databases
            if source in ('from-autocdb', 'to-autocdb'):
                match = os.path.expanduser(match)
                if source == 'from-autocdb':
                    keys = senders
                elif source == 'to-autocdb':
                    keys = [recipient]
                # If the text file doesn't exist, let the exception
                #  happen and get passed back to tmda-filter.
                txtmtime = os.path.getmtime(match)
                # If the cdb file doesn't exist, that's not an error.
                try:
                    cdbmtime = os.path.getmtime(match + '.cdb')
                except OSError:
                    cdbmtime = 0
                valid_cdb = 1
                if cdbmtime <= txtmtime:
                    valid_cdb = Util.build_cdb(match)
                if valid_cdb:
                    found_match = self.__search_cdb(match + '.cdb',
                                                    keys, actions)
                else:
                    found_match = self.__search_file(match, keys, actions)
                if found_match:
                    break
            # ezmlm `subscribers' directories.
            if source in ('from-ezmlm', 'to-ezmlm'):
                match = os.path.expanduser(match)
                if source == 'from-ezmlm':
                    keys = senders
                elif source == 'to-ezmlm':
                    keys = [recipient]
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
            if (source[:len('from-mailman')] == 'from-mailman' or
                source[:len('to-mailman')] == 'to-mailman'):
                match = os.path.expanduser(match)
                (mm_source, mmdb_key) = string.split(source, '.')
                if mm_source == 'from-mailman':
                    keys = senders
                elif mm_source == 'to-mailman':
                    keys = [recipient]
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
                if content and re.search(match,content,(re.M|re.I)):
		    found_match = 1
                    break
            if source in ('body-file','headers-file'):
                match_list = []
                match = os.path.expanduser(match)
                match_list = Util.file_to_list(match,match_list)
                if source == 'body-file' and msg_body:
                    content = msg_body
                elif source == 'headers-file' and msg_headers:
                    content = msg_headers
                else:
                    content = None
                for line in match_list:
                    mo = self.matches.match(line)
                    if mo:
                        expr = mo.group(2) or mo.group(3)
                        if content and re.search(expr,content,(re.M|re.I)):
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
	    line = _rulestr(source, match, actions)
	else:
	    actions = None
	return actions, line


def _rulestr(source, match, actions):
    """
    Build string from source, match and actions.
    """
    if source in ('headers', 'body'):
        match = '(' + str(match) + ')'
    line = str(source) + ' ' + match + ' ' + _actionstr(actions)
    return line


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
		action_line = _cookiestr(action)
		mo = FilterParser.out_action.match(action_line)
		if mo:
		    if len(line) == 0:
			line = line + 'tag'
		    line = line + ' ' + header + ' ' + action_line
    return line


def _cookiestr(action):
    line = str(action[0])
    if action[1]:
	line = line + '=' + str(action[1])
    return line


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
