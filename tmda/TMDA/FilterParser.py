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


class FilterParser:
    def __init__(self):
        self.action = None
        self.action_option = None
 

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
        while 1:
            line = fp.readline()
            if not line:                # exit loop if out of lines
                break
            line = string.strip(line)
            lineno = lineno + 1
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
                if source == 'from':
                    findmatch = Util.findmatch([string.lower(match)],senders)
                elif source == 'to':
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
                    if source == 'from-file':
                        file_match = Util.findmatch(match_list,senders)
                    elif source == 'to-file':
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
                if os.path.exists(match):
                    if source == 'from-dbm':
                        keys = senders
                    elif source == 'to-dbm':
                        keys = [recipient]
                    try:
                        dbm = anydbm.open(match,'c')
                        for key in keys:
                            if dbm.has_key(string.lower(key)):
                                dbm_value = dbm[string.lower(key)]
                                # If there is an entry for this key,
                                # we consider it an overriding action
                                # specification.
                                if dbm_value:
                                    self.action = dbm_value
                                else:
                                    self.action = action
                                break
                    except:
                        pass
                    dbm.close()
            if source in ('body', 'headers'):
                if source == 'body':
                    content = msg_body
                if source == 'headers':
                    content = msg_headers
                if re.search(match,content,(re.M|re.I)):
                    self.action = action
                    break
            if source in ('body-file','headers-file'):
                match_list = []
                match = os.path.expanduser(match)
                if os.path.exists(match):
                    match_list = Util.file_to_list(match,match_list)
                    if source == 'body-file':
                        content = msg_body
                    elif source == 'headers-file':
                        content = msg_headers
                    for expr in match_list:
                        if re.search(expr,content,(re.M|re.I)):
                            self.action = action
                            break
            if source == 'size':
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
