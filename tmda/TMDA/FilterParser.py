# -*- python -*-

"""
TMDA filter file parser.

Filter file syntax documented in htdocs/config-filter.html
"""


import anydbm
import os
import re
import string

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
    def __init__(self, checking=None):
        self.action = None
        self.action_option = None
        self.checking = checking
        

    def read(self, filename):
        """Open and read the named filter file.  Files that cannot be opened
        are silently ignored."""
        self.filterlist = []
        if os.path.exists(filename):
            try:
                fp = open(filename)
            except IOError:
                pass
            self.__parse(fp, filename)
            fp.close()


    def __parse(self, fp, fpname):
        """
        Parse the filter file.  Comment lines, blank lines, and lines
        with invalid syntax are ignored.  The rest are appended to a
        list (self.filterlist) which is where the actual matching will
        take place.
        """
        lineno = 0
        e = None                        # None, or an exception
        while 1:
            line = fp.readline()
            if not line:                # exit loop if out of lines
                break
            lineno = lineno + 1
            line = string.strip(line)
            # comment or blank line?
            if line == '' or line[0] in '#':
                continue
            else:
                line = string.expandtabs(line)
                line = string.split(line, ' #')[0]
                line = string.strip(line)
            # Skip line if it's not composed of exactly 3 elements.
            if len(string.split(line,None)) == 3:
                self.filterlist.append(line)
            else:
                # A non-fatal parsing error occurred.  Set up the
                # exception but keep going. The exception will be
                # raised at the end of the file and will contain a
                # list of all bogus lines.
                if not e and self.checking:
                    e = ParsingError(fpname)
                if self.checking:
                    e.append(lineno, `line`)
        # If any parsing errors occurred and we are running in check
        # mode, raise an exception.
        if e:
            raise e


    def firstmatch(self, recipient, senders=None,
                   msg_body=None, msg_headers=None, msg_size=None):
        """Iterate over each line in the list looking for a match.  As
        soon as a match is found exit, returning the corresponding
        action, action option, and matching line.  Expects each line
        to have valid syntax."""
        line = None
        for line in self.filterlist:
            self.action = None
            self.action_option = None
            (source,match,action) = string.split(line,None)
            source = string.lower(source)
            if source in ('from', 'to'):
                findmatch = None
                if source == 'from' and senders:
                    findmatch = Util.findmatch([string.lower(match)],senders)
                elif source == 'to' and recipient:
                    findmatch = Util.findmatch([string.lower(match)],[recipient])
                if findmatch:
                    self.action = action
                    break
            if source in ('from-file', 'to-file'):
                match_list = []
                match = os.path.expanduser(match)
                if os.path.exists(match):
                    match_list = Util.file_to_list(match,match_list)
                    file_match = None
                    if source == 'from-file' and senders:
                        file_match = Util.findmatch(match_list,senders)
                    elif source == 'to-file' and recipient:
                        file_match = Util.findmatch(match_list,[recipient])
                    if file_match:
                        # The second column of the line may contain an
                        # overriding action specification.
                        if file_match != 1:
                            self.action = file_match
                        else:           
                            self.action = action
                        break
            if source in ('from-dbm', 'to-dbm'):
                match = os.path.expanduser(match)
                if source == 'from-dbm':
                    keys = senders
                elif source == 'to-dbm':
                    keys = [recipient]
                try:
                    dbm = anydbm.open(match,'r')
                    for key in keys:
                        if key and dbm.has_key(string.lower(key)):
                            dbm_value = dbm[string.lower(key)]
                            # If there is an entry for this key,
                            # we consider it an overriding action
                            # specification.
                            if dbm_value:
                                self.action = dbm_value
                            else:
                                self.action = action
                            dbm.close()
                            break
                    if self.action: break
                except anydbm.error:
                    pass
            if source in ('body', 'headers'):
                if source == 'body' and msg_body:
                    content = msg_body
                elif source == 'headers' and msg_headers:
                    content = msg_headers
                else:
                    content = None
                if content and re.search(match,content,(re.M|re.I)):
                    self.action = action
                    break
            if source in ('body-file','headers-file'):
                match_list = []
                match = os.path.expanduser(match)
                if os.path.exists(match):
                    match_list = Util.file_to_list(match,match_list)
                    if source == 'body-file' and msg_body:
                        content = msg_body
                    elif source == 'headers-file' and msg_headers:
                        content = msg_headers
                    else:
                        content = None
                    for expr in match_list:
                        if content and re.search(expr,content,(re.M|re.I)):
                            self.action = action
                            break
                    if self.action: break
            if source == 'size' and msg_size:
                match_list = list(match)
                operator = match_list[0] # first character should be < or >
                bytes = string.join(match_list,'')[1:] # rest is the size
                comparison = None
                if operator == '<':
                    comparison = int(msg_size) < int(bytes)
                elif operator == '>':
                    comparison = int(msg_size) > int(bytes)
                if comparison:
                    self.action = action
                    break
        # Split the action=option apart if possible.
        try:
            (self.action, self.action_option) = string.split(self.action, '=')
        except AttributeError:          # empty action (no matches)
            pass
        except TypeError:               # Python 1.x returns TypeError for above
            pass
        except ValueError:              # empty action_option
            pass
        # Make sure action is all lowercase.
        if self.action:self.action = string.lower(self.action)
        return self.action, self.action_option, line
