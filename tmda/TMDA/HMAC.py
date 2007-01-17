# -*- python -*-
#
# Copyright (C) 2001-2007 Jason R. Mastaler <jason@mastaler.com>
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
HMAC (Keyed-Hashing for Message Authentication) in Python.

Implements the HMAC algorithm for SHA-1 as described by
RFC 2104 (http://www.faqs.org/rfcs/rfc2104.html).

Python >= 2.2 includes a more general purpose HMAC module
(http://www.python.org/doc/current/lib/module-hmac.html).

Based on code from p2.py
<URL:http://www.nightsong.com/phr/crypto/p2.py>
Copyright (C) 2002 Paul Rubin
"""

from array import array
import sha


_ipad="\x36"*64
_opad="\x5C"*64

_itrans = array('B', [0]*256) 
_otrans = array('B', [0]*256)     
for i in xrange(256): 
    _itrans[i] = i ^ 0x36 
    _otrans[i] = i ^ 0x5c 
_itrans = _itrans.tostring() 
_otrans = _otrans.tostring() 

newh = sha.new

class hmac:
    def __init__(self, k, m=None):
        if isinstance(k, hmac):
            self.inner = k.inner.copy()
            self.outer = k.outer.copy()
        else:
            self.outer = newh()
            self.inner = newh()
            if len(k) > 64:
                k=newh(k).digest()
            k = k + chr(0)*(64-len(k))
            self.inner.update((k.translate(_itrans)+_ipad)[:64])
            self.outer.update((k.translate(_otrans)+_opad)[:64])
            if (m):
                self.update(m)
    def update(self, m):
        self.inner.update(m)
    def digest(self):
        h=self.outer.copy()
        h.update(self.inner.digest())
        return h.digest()

def new(k, m=None):
    return hmac(k, m)
