# -*- python -*-

"""
TMDA filter file parser.

Filter files are used to control mail both coming in to and going out
of TMDA.  For incoming, the filter controls how the message is
disposed of.  For outgoing, it controls how the message is tagged.
Lines are read sequentially from top to bottom, and the first match
wins.

Each line of a filter file is expected to a string containing three
fields separated by whitespace.  Everything after '#' on a line is
considered a comment and ignored.  Blank lines and lines with invalid
syntax are also ignored:

<source> <match> <action>

<source> specifices where to look for a match and can be one of:

  to (look for the match in the next field)
  to-file (look for the match in a textfile)
  to-dbm (look for the match in a DBM-style database)
  
<match> contains either the address or expression to match against, or
the location of the address or expression to match against.  It should
be either an e-mail address, a wildcard expression, or the full path
to a textfile or DBM database.

- Textfiles can contain one or two fields separated by whitespace.
The first field should be the address or wildcard to match against,
and the optional second field is an overriding action.

- DBM records should contain the address to match against as the key,
and an optional overriding action as the value.

<action> specifies what action to take on the message.  An optional `='
separates the action from the action's option.  Possible values for
<action> differ based on whether the message is incoming or outgoing.

  For incoming filters, <action> can be one of:
    ???
    
  For outgoing filters, <action> can be one of:
    bare
    sender
    dated
    dated=timeout_interval
    exp=full_address (aliases for 'exp' include 'as' and 'explicit')
    ext=address_extension (aliases for 'ext' include 'extension')
    kw=keyword (aliases for 'kw' include 'keyword')

Examples:

# outgoing filter file
to foo@mastaler.com dated
to bar@mastaler.com dated=6M
to *@=gnus.org exp=jason@gnus.org
to-file ~/.lists ext=mlists # jason-mlists@mastaler.com
to-dbm /var/tmp/whitelist.db bare

"""


import anydbm
import os
import string
import sys

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


    def firstmatch(self, address):
        """Iterate over each line in the list looking for a match
        for address.  As soon as a match is found exit, returning the
        corresponding action and action option.
        Expects each line to have valid syntax"""
        for line in self.filterlist:
            self.action = None
            self.action_option = None
            (source,match,action) = string.split(line,None)
            source = string.lower(source)
            if source == 'to':
                if Util.findmatch([string.lower(match)],address):
                    self.action = action
                    break
            if source == 'to-file':
                match_list = []
                match = os.path.expanduser(match)
                if os.path.exists(match):
                    match_list = Util.file_to_list(match,match_list)
                    file_match = Util.findmatch(match_list,address)
                    if file_match:
                        # The second column of the line may contain an
                        # overriding action specification.
                        if file_match != 1:
                            self.action = file_match
                        else:           
                            self.action = action
                        break
            if source == 'to-dbm':
                match = os.path.expanduser(match)
                if os.path.exists(match):
                    try:
                        dbm = anydbm.open(match,'c')
                        if dbm.has_key(string.lower(address)):
                            dbm_value = dbm[string.lower(address)]
                            # If there is an entry for this address,
                            # we consider it an overriding action
                            # specification.
                            if dbm_value:
                                self.action = dbm_value
                            else:
                                self.action = action
                            break
                    except error:
                        pass
                    dbm.close()
        # Split the action=option apart if possible.
        try:
            (self.action, self.action_option) = string.split(self.action, '=')
        except AttributeError:          # empty action (no matches)
            pass
        except ValueError:              # empty action_option
            pass
        # Make sure action is all lowercase.
        if self.action:self.action = string.lower(self.action)
        return self.action, self.action_option
