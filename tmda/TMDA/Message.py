# -*- python -*-
#
# Copyright (C) 2001,2002,2003 Jason R. Mastaler <jason@mastaler.com>
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

"""Standard TMDA Message Object"""


from cStringIO import StringIO
from email.Generator import Generator
from email.Parser import Parser
import email.Message


class Message(email.Message.Message):
    """Inherit from email.Message so we can override some methods
    whose behavior we need to change."""
    def __init__(self):
        email.Message.Message.__init__(self)

    def as_string(self, unixfrom=0):
        fp = StringIO()
        g = Generator(fp, mangle_from_=0) # don't escape From
        g.flatten(self, unixfrom=unixfrom)
        return fp.getvalue()

    
def message_from_file(fp, _class=None, strict=0):
    if _class is None:
        _class = Message
    return Parser(_class, strict=strict).parse(fp)

def message_from_string(s, _class=None, strict=0):
    if _class is None:
        _class = Message
    return Parser(_class, strict=strict).parsestr(s)
