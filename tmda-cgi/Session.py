#!/usr/bin/env python
#
# Copyright (C) 2002 Gre7g Luterman <gre7g@wolfhome.com>
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

"Generic session handler."

import glob
import os
import pickle
import pwd
import random
import re
import string
import sys
import time
import CgiUtil

from TMDA import Util

Rands = random.Random()

# Constants
CGI_SESSION_PREFIX = "/tmp/TMDASess."

class Session:
  """Sessioning tool for use in CGI.

Resurrect an old session by passing a form with the session ID (SID) into the 
constructor.  An empty object will be created if the session has expired.  A new
session will be created if the form does not specify a (valid) SID.

Instantiating a session will check Form["user"] and Form["password"] if they 
exist to establish Session["UID"].  To check the validity of a session, test 
Session.has_key("UID") before any action that might reveal sensative 
information.

Once a session is validated, the module will switch EUID to Session["UID"].

The session's SID is saved as member SID.

Session data is stored in the object by treating it as a dictionary.  For
example:
  A = Session(Form)
  A['key'] = value
  A.Save()
  print "http://some/url?SID=%s" % A.SID

The Save() member saves the session's current values on disk, but can only be 
called once a validated session has been established.  Writes are done as 
CGI_USER, as specified in Defaults."""

  def __suid__(self, UID = None, GID = None):
    """Try to change to a new user.

Report an error if we can't, but should be able to."""
    if os.environ["TMDA_CGI_MODE"] == "system-wide":
      # If not specified, use misc. user info
      if not UID:
        PasswordRecord  = pwd.getpwnam(os.environ["TMDA_CGI_USER"])
        UID = PasswordRecord[2]
        GID = PasswordRecord[3]
        if not UID:
          CgiUtil.TermError("CGI_USER is UID 0.", """It is not safe to allow
root to process session files.""", "set euid",
            "CGI_USER = %s" % os.environ["TMDA_CGI_USER"], "Recompile CGI.")

      try:
        os.seteuid(0)
        os.setegid(0)
        os.setegid(GID)
        os.seteuid(UID)
      except OSError:
        CgiUtil.TermError("Cannot SUID.", """File permissions on the CGI have
been changed or the CGI is located in a nosuid partition.""", "set euid",
          CgiUtil.FileDetails("CGI", sys.argv[0]),
          """Recheck the CGI's permissions and owner.  The file permissions
should be 4755 (-rwsr-xr-x) and the owner should be root.<br>Also check in which
partition you placed the CGI.  You cannot run the CGI in system-wide mode if
its partition is marked "nosuid" in /etc/fstab.""")

  def __init__(self, Form):
    "Reload an existing SID or create a new one."
    
    global Defaults

    # Existing, valid looking session?
    if Form.has_key("SID") and \
      re.compile("^[a-zA-Z0-9]{8}$").search(Form["SID"].value):
      self.SID = Form["SID"].value

      # Resurrect session
      try:
        self.__suid__()
        if os.stat(CGI_SESSION_PREFIX + self.SID).st_uid != os.geteuid():
          CgiUtil.TermError("CGI_USER does not own session file.",
            "Something suspicious is going on here.  This should not happen.",
            "open file",
            CgiUtil.FileDetails("Session data", CGI_SESSION_PREFIX + self.SID),
            "No recommendation.")
        F = open(CGI_SESSION_PREFIX + self.SID)
        self.Vars = pickle.load(F)
        F.close()
        self.__suid__(self.Vars["UID"], self.Vars["GID"])
        os.environ["HOME"] = self.Vars["HOME"]
        os.environ["USER"] = self.Vars["User"]
        
        # Make sure the session has not been hijacked
        if os.environ["REMOTE_ADDR"] != self.Vars["IP"]:
          CgiUtil.TermError("User's IP address has changed.",
            "Your IP address has changed. This is not allowed.",
            "read session data", "%s->%s" %
            (self.Vars["IP"], os.environ["REMOTE_ADDR"]), "Log back in.")
        
        # Is there a TMDARC variable?
        if os.environ.has_key("TMDARC"):
          # Yes, replace it
          os.environ["TMDARC"] = os.environ["TMDARC"].replace("/~/",
            "/%s/" % self.Vars["User"])
        
        # Now that we know who we are, get our defaults
        from TMDA import Defaults
      except IOError: # Failed to resurrect session, fall through to make new SID
        pass
      return
      
    # New session
    SessionChars = string.ascii_letters + string.digits
    self.SID = ""
    for i in range(8):
      self.SID += SessionChars[Rands.randrange(len(SessionChars))]
    self.Vars = {}
    if Form.has_key("user"):
      if os.environ.has_key("TMDA_VLOOKUP"):
        VLookup = os.environ["TMDA_VLOOKUP"]
      else:
        VLookup = None
      try:
        self.Vars["HOME"], UID, self.Vars["GID"] = \
          Util.getuserparams(Form["user"].value, VLookup)
      except KeyError:
        return
      if not UID:
        PasswordRecord = pwd.getpwnam(os.environ["TMDA_VUSER"])
        UID = PasswordRecord[2]
        GID = PasswordRecord[3]
      os.environ["HOME"] = self.Vars["HOME"]

    # Logging in?
    if not Form.has_key("user"): return

    # Is there a TMDARC variable?
    if os.environ.has_key("TMDARC"):
      # Yes, replace it
      os.environ["TMDARC"] = os.environ["TMDARC"].replace("/~/",
        "/%s/" % Form["user"].value)

    # Initialize the auth mechanism
    import Authenticate
    try:
      if os.environ.has_key( "TMDA_AUTH_TYPE" ):
        if os.environ["TMDA_AUTH_TYPE"] == "program":
          Authenticate.InitProgramAuth( os.environ["TMDA_AUTH_ARG"] )
        elif os.environ["TMDA_AUTH_TYPE"] == "remote":
          Authenticate.InitRemoteAuth( os.environ["TMDA_AUTH_ARG"] )
        elif os.environ["TMDA_AUTH_TYPE"] == "file":
          Authenticate.InitFileAuth( os.environ["TMDA_AUTH_ARG"] )
      else:
        # Default to regular flat file.
        # Order of preference:
        #   1) $TMDARC/tmda-cgi
        #   2) $HOME/tmda-cgi
        #   3) /etc/tmda-cgi
        if os.environ.has_key("TMDARC"):
          File = os.path.join(os.path.split(os.environ["TMDARC"])[0],
                              "tmda-cgi")
        else:
          File = os.path.join(self.Vars["HOME"], ".tmda/tmda-cgi")
        try:
          os.seteuid(0)
          os.setegid(0)
        except OSError:
          pass
        if not Util.CanRead( File, UID, self.Vars["GID"], 0 ):
          File = "/etc/tmda-cgi"

        Authenticate.InitFileAuth( File )
    except ValueError, err:
      if os.environ.has_key("TMDA_AUTH_TYPE"):
        AuthType = os.environ["TMDA_AUTH_TYPE"]
      else:
        AuthType = "<b><i>not set</i></b>"
      CgiUtil.TermError( "Auth Initialization Failed", "ValueError caught", 
        "init auth type %s" % AuthType, err, "Fix the code." )

    # Validate the new session
    if not Form.has_key("password"): return
    if Authenticate.CheckPassword(Form):
      self.Vars["UID"]   = UID
      self.Vars["User"]  = Form["user"].value
      self.__suid__(self.Vars["UID"], self.Vars["GID"])
      os.environ["USER"] = self.Vars["User"]
      self.Vars["IP"]    = os.environ["REMOTE_ADDR"]
      self.Vars["debug"] = Form["debug"].value

      # Now that we know who we are, get our defaults
      from TMDA import Errors
      try:
        from TMDA import Defaults
      except Errors.ConfigError, (ErrStr):
        CgiUtil.TermError("ConfigError", ErrStr, "import Defaults",
          "", """Recheck the CGI's permissions and owner.  The file permissions
should be 4755 (-rwsr-xr-x) and the owner should be root for system-wide
install or a non-privileged user for single-user mode.<br>Also check in which
partition you placed the CGI.  You cannot run the CGI in system-wide or single-
user modes if its partition is marked "nosuid" in /etc/fstab.""")

      # Test CGI_ACTIVE
      if not Defaults.CGI_ACTIVE:
        CgiUtil.TermError("<tt>CGI_ACTIVE</tt> has not been set to 1.",
          "Incomplete configuration file.", "read configuration files",
          "%s<br>%s" %
          (CgiUtil.FileDetails("Global configuration", Defaults.GLOBAL_TMDARC),
          CgiUtil.FileDetails("Local configuration", Defaults.TMDARC)),
          """Add <tt>CGI_ACTIVE = 1</tt> to one of the configuration files or
modify<br>file permissions to allow them to be read.""")

      self.Vars["CLEANUP"] = Defaults.CGI_CLEANUP_ODDS;
      self.Save() # Save session & set user
    self.__suid__()

  def Save(self):
    """Save all session variables to disk and change user.  Possibly clean up 
old sessions."""
    self.__suid__()
    try:
      F = open(CGI_SESSION_PREFIX + self.SID, "w")
      pickle.dump(self.Vars, F)
      F.close()
    except IOError:
      CgiUtil.TermError("<tt>CGI_USER</tt> is incorrectly configured.",
        "Incomplete configuration file.", "read configuration files",
        "%s<br>%s" %
        (CgiUtil.FileDetails("Global configuration", Defaults.GLOBAL_TMDARC),
        CgiUtil.FileDetails("Local configuration", Defaults.TMDARC)),
        """Add <tt>CGI_USER = "UserName"</tt> to one of the configuration files
or modify<br>file permissions to allow them to be read.  For <tt>UserName</tt>,
use the user name<br>configured into your web server.  For Apache, look for the
<tt>User</tt> directive.  You may need to recompile the CGI.""")

    # Clean up?
    if self.Vars.has_key("CLEANUP") and \
      (Rands.random() < self.Vars["CLEANUP"]):
      # Go through all sessions and check a-times
      Sessions = glob.glob(CGI_SESSION_PREFIX + "*")
      for Session in Sessions:
        try: # these commands could fail if another thread cleans simultaneously
          Stats = os.stat(Session)
          # Expired?
          if Stats[7] + Defaults.CGI_SESSION_EXP < time.time():
            os.unlink(Session)
        except OSError:
          pass

    # Change back to regular user
    self.__suid__(self.Vars["UID"], self.Vars["GID"])

  def __contains__(self, a): return a in self.Vars
  def countOf(self): return len(self.Vars)
  def __delitem__(self, a): del self.Vars[a]
  def __getitem__(self, a): return self.Vars[a]
  def __setitem__(self, a, b): self.Vars[a] = b
  def keys(self): return self.Vars.keys()
  def has_key(self, a): return self.Vars.has_key(a)
