#!/usr/bin/env python
#
# Copyright (C) 2003 Gre7g Luterman <gre7g@wolfhome.com>
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

"""An object that creates a stream and captures anything piped into it.

Usage:
S = StreamCapture()
print >> S.Stream, "Capture this!"
S.Stream.close()
print S.GetCapture()

Streams are opened when the class is instantiated and are only returned when
the stream is closed.  Trying to read the stream before it has been closed will
cause the program to hang."""

import os
import thread

def __Capture__(self):
  self.Captured = self.Read.readlines()
  self.Lock.release()

class StreamCapture:
  Captured = None
  
  def __init__(self):
    # Create stream
    R_FD, W_FD  = os.pipe()
    self.Stream = os.fdopen(W_FD, "w")
    self.Read   = os.fdopen(R_FD)
    self.Lock   = thread.allocate_lock()
    
    # Lock is used to make sure the stream is done
    self.Lock.acquire()
    thread.start_new_thread(__Capture__, (self,))
  
  def GetCapture(self):
    self.Lock.acquire()
    RetVal = self.Captured
    self.Lock.release()
    return RetVal
