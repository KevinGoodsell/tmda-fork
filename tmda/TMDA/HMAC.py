# -*- python -*-

"""
HMAC (Keyed-Hashing for Message Authentication) Python module.

Written by Reuben Sumner <rasumner@iname.com>
Modified by Jason R. Mastaler <jason@mastaler.com> for use with TMDA.

Implements the HMAC algorithm for either SHA-1 or MD5 as described by
RFC 2104.

For all the relevant papers and RFCs see:
<http://www-cse.ucsd.edu/users/mihir/papers/hmac.html>
"""

import string

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
    #return "".join(map(lambda x,y: chr(ord(x) ^ ord(y)),a,b))
    return string.join(map(lambda x,y: chr(ord(x) ^ ord(y)),a,b), '')
        
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

