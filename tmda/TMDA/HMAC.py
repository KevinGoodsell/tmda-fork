# -*- python -*-
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
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
HMAC (Keyed-Hashing for Message Authentication) Python module.

Written by Reuben Sumner <rasumner@iname.com>
Modified by Jason R. Mastaler <jason@mastaler.com> for use with TMDA.

Implements the HMAC algorithm for either SHA-1 or MD5 as described by
RFC 2104.

For all the relevant papers and RFCs see:
<http://www-cse.ucsd.edu/users/mihir/papers/hmac.html>
"""

# For MD5         #  For SHA-1
####################################
# import md5      #  import sha
# _L=16           #  _L=20
# newh = md5.new  # newh = sha.new

import sha # choose md5 or sha, update B,L as necessary
newh = sha.new

_B=64 # byte length of basic compression block (SHA & MD5)
_L=20 # byte length of digest size (SHA=20, MD5=16)

_ipad="\x36"*_B
_opad="\x5C"*_B

def _strxor(a,b):
    return "".join(map(lambda x,y: chr(ord(x) ^ ord(y)),a,b))
        
class hmac:
    "RFC2104 HMAC class"
    def __init__(self,k,m=None):
        if isinstance(k,hmac): # for cloning
            self.inner = k.inner.copy()
            self.outer = k.outer.copy()
        else:
            self.outer = newh()
            self.inner = newh()
            if len(k) > _B:
                k=newh(k).digest()
            k = k + chr(0)*(_B-len(k))
            self.outer.update(_strxor(k,_opad))
            self.inner.update(_strxor(k,_ipad))
            if (m):
                self.update(m)
    def update(self,m):
        self.inner.update(m)
    def digest(self):
        h=self.outer.copy()
        h.update(self.inner.digest())
        return h.digest()
    def copy(self):
        return hmac(self)

def new(k,m=None): return hmac(k,m)

