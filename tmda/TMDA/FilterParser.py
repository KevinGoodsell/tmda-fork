# -*- python -*-

"""
TMDA filter file parser.

Filter files are used to control mail both coming in to and going out
of TMDA.  For incoming, the filter controls how the message is
disposed of.  For outgoing, it controls how the message is tagged.
Lines are read sequentially from top to bottom, and the first match
wins.

Each line of a filter file is expected to be a string containing three
unquoted fields separated by whitespace.  Everything after '#' on a
line is considered a comment and ignored.  Blank lines and lines with
invalid syntax are also ignored:

<source> <match> <action>

* <source> specifices the source of the match and can be one of:

incoming & outgoing:
  to (recipient address)
  to-file
  to-dbm

incoming only:
  from (sender address)
  from-file
  from-dbm
  body (message body)
  body-file
  headers (message headers)
  headers-file
  size (message size)

* <match> should be an unquoted expression, or the full path to a
  textfile or DBM database containing unquoted expressions if <source>
  was suffixed with `-file' or `-dbm'.

to* = recipient e-mail address or wildcard expression.
from* = sender e-mail address or wildcard expression.
body* = regular expression matching message body content.
headers* = regular expression matching message header content.
size = a comparison operator and number of bytes to compare to the
       size of the message.  Only `<' and `>' are supported.

NOTE: The second field in a textfile or DBM is optional, but overrides
<action> if present.

* <action> specifies what action to take on the message.  An optional
  `=' separates the action from the action's option.  Possible values
  differ based on whether the message is incoming or outgoing.

  For incoming filters, <action> can be one of:
    bounce (bounce the message)
    drop (silently drop the message)
    ok (deliver the message)
    confirm (request confirmation for the message)

  Incoming <action> aliases:
    reject for bounce
    exit and stop for drop
    accept and deliver for ok

  Incoming examples:
    # incoming filter file
    to postmistress@mastaler.com ok
    from *@=badboy.dom bounce
    from-file ~/.tmda/lists/whitelist accept
    from-dbm /var/tmp/blacklist drop
    body (viagra|ginseng) confirm
    headers (Precedence:.*junk) reject
    size <1000 accept
    size >100000 stop


  For outgoing filters, <action> can be one of:
    bare (don't tag)
    bare=append (don't tag, and also add recipient to Defaults.BARE_APPEND)
    sender (tag with a sender address)
    dated (tag with a dated address)
    dated=timeout_interval 
    exp=full_address (use an explicit address)
    ext=address_extension (add an extension to the address)
    kw=keyword (tag with a keyword address)

  Outgoing <action> aliases:
    as and explicit for exp
    extension for ext
    keyword for kw

  Outgoing examples:
    # outgoing filter file
    to foo@mastaler.com dated
    to bar@mastaler.com dated=6M
    to *@=gnus.org exp=jason@gnus.org
    to-file ~/.lists ext=mlists # jason-mlists@mastaler.com
    to-dbm /var/tmp/whitelist.db bare

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
