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

"Global config file viewer for tmda-cgi."

import binascii
import glob
import os
import re
import sys
import time

import CgiUtil
import Template

from TMDA import Errors

PermSearch = re.compile("^([^#\s]\S*)\s+(\d+)")

def KeyGen():
  # Generate a random key
  RandomDev = "/dev/urandom"
  if os.path.exists(RandomDev):
    Key = open(RandomDev, "rb").read(20)
  else:
    # Otherwise generate some pseudo-random data from the system
    # and use the SHA of resulting key as the key.
    import sha
    import commands
    Unpredictable = ( "date", "fstat", "iostat", "vmstat", "finger", "ps -la",
      "netstat", "uname -a", "cat /etc/passwd", "cat /etc/aliases",
      "cat /proc/interrupts" )
    KeyData = ""
    for i in Unpredictable:
      if commands.getstatusoutput(i)[0] == 0:
        KeyData += os.popen(i).read()
    Key = sha.new(KeyData + "key").digest()
  return binascii.hexlify(Key)

def FindFiles(Path, AbsPath):
  "Find all files in a given path and expand variables."
  Files = os.listdir(AbsPath)
  RetVal = []
  for File in Files:
    if (File != "CVS") and (File != "permissions.ini"):
      FilePath = os.path.join(Path, File)
      AbsFilePath = os.path.join(AbsPath, File)
      L = len(RetVal)
      if os.path.isdir(AbsFilePath):
        RetVal[L:L] = FindFiles(FilePath, AbsFilePath)
      else:
        RetVal[L:L] = [FilePath]
  return RetVal

def FindExisting(Files, Path):
  "Find which of the given files exist."
  RetVal = []
  for File in Files:
    TargFile = File % Dict
    if os.path.isfile(os.path.join(Path, TargFile)):
      RetVal.append(TargFile)
  return RetVal

def CreateTgz(Archive, Filelist):
  """Create a .tgz of the listed files, but take care with ../ files.

Return 0 on success, error code on error."""

  Files = []
  Parents = []
  for Filename in Filelist:
    SrcFn = os.path.join(os.environ["HOME"], Filename)
    if os.path.isfile(SrcFn):
      if Filename[:3] == "../":
        try:
          os.mkdir(os.path.join(os.environ["HOME"], "%(Parent)s"))
        except OSError:
          pass
        NewFilename = "%(Parent)s/" + Filename[3:]
        DstFn = os.path.join(os.environ["HOME"], NewFilename)
        Parents.append((SrcFn, DstFn))
        os.rename(SrcFn, DstFn)
        Files.append(NewFilename)
      else:
        Files.append(Filename)
  TarCmd = "%s -C %s -czf %s %s" % (PVars[("NoOverride", "WhichTar")],
    os.environ["HOME"], Archive, " ".join(Files))
  RetVal = os.system(re.sub("([\(\)])", r"\\\1", TarCmd))
  if RetVal:
    CgiUtil.TermError("CreateTgz failed.", "Errcode: %D" % RetVal,
      "create backup", re.sub("([\(\)])", r"\\\1", TarCmd),
      "Check file permissions in home directory.")
  for (DstFn, SrcFn) in Parents:
    os.rename(SrcFn, DstFn)
  try:
    os.rmdir(os.path.join(os.environ["HOME"], "%(Parent)s"))
  except OSError:
    pass

def ReadTgz(Archive):
  "Return the files listed in an archive."
  Files = os.popen("%s -C %s -tzf %s" % (PVars[("NoOverride", "WhichTar")],
    os.environ["HOME"], Archive)).readlines()
  for i in range(len(Files)):
    Files[i] = Files[i].strip()
  return Files

def ExtractTgz(Archive):
  """Extract all from a .tgz, but take care with ../ files.

Return file list on success, None on error."""

  if os.system("%s -C %s -xzf %s" % (PVars[("NoOverride", "WhichTar")], 
    os.environ["HOME"], Archive)):
    return None
  Files = ReadTgz(Archive)
  for i in range(len(Files)):
    if Files[i][:11] == "%(Parent)s/":
      NewFilename = "../" + Files[i][11:]
      SrcFn = os.path.join(os.environ["HOME"], Files[i])
      DstFn = os.path.join(os.environ["HOME"], NewFilename)
      os.rename(SrcFn, DstFn)
      Files[i] = NewFilename
  try:
    os.rmdir(os.path.join(os.environ["HOME"], "%(Parent)s"))
  except OSError:
    pass
  return Files

def CheckDir(Filename):
  "Make sure directory exists to hold file."

  Dirs = []
  while 1:
    Filename = os.path.split(Filename)[0]
    if os.path.isdir(Filename): break
    Dirs.append(Filename)
  while len(Dirs):
    os.mkdir(Dirs.pop())

def Revert(Files, Backup, ErrStr):
  "Revert back to system before install."

  for File in Files: os.unlink(File)
  if Backup:
    ExtractTgz(Backup)
  try:
    os.unlink(Backup)
  except OSError:
    pass
  CgiUtil.TermError("Install aborted.", ErrStr, "install TMDA",
    "", "Check file permissions in home directory.")

def ListDiff(a, b):
  "Take all items in b out of a."
  try:
    i = 0
    while 1:
      if (a[i] % Dict) in b:
        del a[i]
      else:
        i += 1
  except IndexError:
    pass

def CopyFiles(FilesToCopy, SrcDir, Backup):
  """Copy files from SrcDir into User's home dir.  Revert to Backup on failure.

This routine may modify the list if a parent file could not be copied.  Such
files will be removed."""

  # Keep track of files copied so we can kill them on a failure
  Copied = []
  Failed = []

  # Copy each file
  for File in FilesToCopy:
    # Get file
    Filename = os.path.join(SrcDir, File)
    F = open(Filename)
    Contents = F.read()
    F.close()

    # Put file
    Filename = os.path.join(os.environ["HOME"], File) % Dict
    try:
      CheckDir(Filename)
      F = open(Filename, "w")
      F.write(Contents % Dict)
      F.close()
      Copied.append(Filename)
    except IOError, (ErrStr):
      # Don't freak out over writes to parent directory
      if (File[:3] == "../") or (File[:11] == "%(Parent)s/"):
        Failed.append(File % Dict)
      else:
        # Install failed, revert!
        Revert(Copied, Backup, "Saving file: %s<br>%s" % (Filename, ErrStr))
    except (ValueError, TypeError), (ErrStr):
      # Install failed, revert!
      Revert(Copied, Backup, "Expanding %%'s in: %s<br>%s" % (Filename,
        ErrStr))
  ListDiff(FilesToCopy, Failed)

def SetPerms(SrcDir, Files, Backup):
  "Set permissions as listed in permissions.ini"

  # Read in permission instructions
  try:
    F = open(os.path.join("skel", SrcDir, "permissions.ini"))
    Lines = F.readlines()
    F.close()
  except IOError:
    return

  # Parse and execute instructions
  try:
    for Line in Lines:
      Match = PermSearch.search(Line)
      if Match:
        os.chmod(os.path.join(os.environ["HOME"], Match.group(1)),
          eval("0" + Match.group(2)))
  except OSError, (ErrStr):
    Revert(Files, Backup, "Setting permission %s on: %s<br>%s" % \
      (Match.group(2), Match.group(1), ErrStr))

def Install():
  "Do the actual installation."

  # What files do we need to install?
  InstallDir = os.path.join(os.getcwd(), "skel", "install")
  FilesToInstall = FindFiles("", InstallDir)

  # What files will that clobber?
  FilesClobbered = FindExisting(FilesToInstall, os.environ["HOME"])

  # Archive the files
  Backup = os.path.join(os.environ["HOME"],
    PVars[("NoOverride", "InstallBackupTGZ")])
  if len(FilesClobbered):
    CreateTgz(Backup, FilesClobbered)
  elif os.path.isfile(Backup):
    os.unlink(Backup)
    Backup = None

  # Copy files from skeleton
  CopyFiles(FilesToInstall, InstallDir, Backup)

  # Expand filenames
  for i in range(len(FilesToInstall)):
    FilesToInstall[i] = FilesToInstall[i] % Dict

  # Set file permissions
  SetPerms("install", FilesToInstall, Backup)

  # Unlink any restore file
  Archive = os.path.join(os.environ["HOME"],
    PVars[("NoOverride", "UninstallBackupTGZ")])
  if os.path.isfile(Archive):
    try:
      os.unlink(Archive)
    except OSError:
      pass

  # Try to import Defaults again.
  try:
    from TMDA import Defaults
  except Errors.ConfigError:
    Revert(FilesToInstall, Backup, "Re-importing Defaults<br>%s" % ErrStr)

  # Prepare template
  T = Template.Template("installed.html")
  T["EMail"] = "%s@%s" % (Defaults.USERNAME, Defaults.HOSTNAME)
  Row = T["Row"]
  if len(FilesClobbered):
    # List files clobbered
    for Filename in FilesClobbered:
      T["Filename"] = Filename
      Row.Add()
    T["Archive"] = PVars[("NoOverride", "InstallBackupTGZ")]
  else:
    # Hide message if no files clobbered
    T["OverWritten"]
  if PVars.has_key(["NoOverride", "InstallInstruct"]):
    T["Instruct"] = PVars[("NoOverride", "InstallInstruct")]
  else:
    T["Instruct"] = T["NoneInstruct"]

  # Show template
  print T

  # Load any initial variables
  raise CgiUtil.JustLoggedIn, ("New install", PVars)

def Uninstall():
  "Do the actual uninstallation."

  # What files do we need to uninstall?
  InstallDir = os.path.join(os.getcwd(), "skel", "install")
  RemoveFiles = FindFiles("", InstallDir)
  for i in range(len(RemoveFiles)):
    RemoveFiles[i] = RemoveFiles[i] % Dict

  # Archive the files
  Backup = os.path.join(os.environ["HOME"],
    PVars[("NoOverride", "UninstallBackupTGZ")])
  CreateTgz(Backup, RemoveFiles)

  # Erase files
  for File in RemoveFiles:
    try:
      Filename = os.path.join(os.environ["HOME"], File)
      os.unlink(Filename)
    except OSError, (ErrStr):
      if File[:3] != "../":
        Revert([], Backup, "Erasing: %s<br>%s" % (Filename, ErrStr))

  # What files do we need to install?
  UninstallDir = os.path.join(os.getcwd(), "skel", "uninstall")
  UninstallFiles = FindFiles("", UninstallDir)

  # Don't clobber anything.
  FilesClobbered = FindExisting(UninstallFiles, os.environ["HOME"])
  ListDiff(UninstallFiles, FilesClobbered)

  # Copy files from skeleton
  CopyFiles(UninstallFiles, UninstallDir, Backup)

  # Unlink any empty directories used
  Dirs = {}
  for File in RemoveFiles:
    File = os.path.join(os.environ["HOME"], File)
    while 1:
      File = os.path.split(File)[0]
      if File and (File != "/"):
        Dirs[File] = None
      else:
        break
  Dirs = Dirs.keys()
  Dirs.sort()
  while len(Dirs):
    Dir = Dirs.pop()
    try:
      os.rmdir(Dir)
    except OSError:
      pass

  # Restore old files if any
  Archive = os.path.join(os.environ["HOME"],
    PVars[("NoOverride", "InstallBackupTGZ")])
  if os.path.isfile(Archive):
    RestoredFiles = ExtractTgz(Archive)
    if not RestoredFiles:
      Revert([], Backup, "Unable to restore old backup: %s" % Archive)
    try:
      os.unlink(Archive)
    except OSError:
      pass
    ListDiff(UninstallFiles, RestoredFiles)
  else:
    Archive = None

  # Prepare template
  from TMDA import Defaults
  T = Template.Template("uninstalled.html")
  T["EMail"] = "%s@%s" % (Defaults.USERNAME, Defaults.HOSTNAME)
  T["Archive"] = PVars[("NoOverride", "UninstallBackupTGZ")]
  Row    = T["Row"]
  AddRow = T["AddRow"]
  if Archive:
    # List files restored
    for Filename in RestoredFiles:
      T["Filename"] = Filename
      Row.Add()
  else:
    # Hide message if no files restored
    T["Restored"]
  if len(UninstallFiles):
    # List files added
    for Filename in UninstallFiles:
      T["Filename"] = Filename % Dict
      AddRow.Add()
  else:
    # Hide message if no files added
    T["Added"]
  if PVars.has_key(["NoOverride", "UninstallInstruct"]):
    T["Instruct"] = PVars[("NoOverride", "UninstallInstruct")]
  else:
    T["Instruct"] = T["NoneInstruct"]

  # Show template
  print T
  sys.exit()

def ReleaseAndDelete(Days):
  """Release all messages younger than given days old.  Delete rest.

Don't release anything if Days=0, release them all if Days=-1."""

  from TMDA import Defaults
  from TMDA import Pending

  # Release
  if Days:
    if Days == -1:
      Threshold = None
      Younger   = None
    else:
      Threshold = "%dd" % Days
      Younger   = 1
    Pending.Queue(dispose = "release", threshold = Threshold, younger = 
      Younger, verbose = 0).initQueue().mainLoop()

  # Wait for messages to release...
  while 1:
    time.sleep(1)
    Queue = Pending.Queue(threshold = Threshold, younger = Younger)
    Queue.initQueue()
    if len(Queue.listPendingIds()) == 0:
      break

  # Delete
  Pending.Queue(dispose = "delete", verbose = 0).initQueue().mainLoop()

  # Tidy-up
  Dir = CgiUtil.ExpandUser(Defaults.RESPONSE_DIR)
  for Filename in glob.glob(os.path.join(Dir, "*.*.*")):
    try:
      os.unlink(Filename)
    except OSError:
      pass
  try:
    os.rmdir(Dir)
  except OSError:
    pass
  Filename = CgiUtil.ExpandUser(Defaults.PENDING_CACHE)
  try:
    os.unlink(Filename)
  except OSError:
    pass
  Dir = os.path.join(Defaults.DATADIR, "pending")
  try:
    os.rmdir(Dir)
  except OSError:
    pass

def Restore():
  "Restore a previous installation."
  Archive = os.path.join(os.environ["HOME"],
    PVars[("NoOverride", "UninstallBackupTGZ")])
  FilesToInstall = ReadTgz(Archive)

  # What files will that clobber?
  FilesClobbered = FindExisting(FilesToInstall, os.environ["HOME"])

  # Archive the files
  Backup = os.path.join(os.environ["HOME"],
    PVars[("NoOverride", "InstallBackupTGZ")])
  if len(FilesClobbered):
    CreateTgz(Backup, FilesClobbered)
  elif os.path.isfile(Backup):
    os.unlink(Backup)
    Backup = None

  # Extract files from archive
  ExtractTgz(Archive)

  # Expand filenames
  for i in range(len(FilesToInstall)):
    FilesToInstall[i] = FilesToInstall[i] % Dict

  # Unlink any restore file
  try:
    os.unlink(Archive)
  except OSError:
    pass

  # Try to import Defaults again.
  try:
    from TMDA import Defaults
  except Errors.ConfigError:
    Revert(FilesToInstall, Backup, "Re-importing Defaults<br>%s" % ErrStr)

  # Prepare template
  T = Template.Template("installed.html")
  T["EMail"] = "%s@%s" % (Defaults.USERNAME, Defaults.HOSTNAME)
  Row = T["Row"]
  if len(FilesClobbered):
    # List files clobbered
    for Filename in FilesClobbered:
      T["Filename"] = Filename
      Row.Add()
    T["Archive"] = PVars[("NoOverride", "InstallBackupTGZ")]
  else:
    # Hide message if no files clobbered
    T["OverWritten"]
  if PVars.has_key(["NoOverride", "InstallInstruct"]):
    T["Instruct"] = PVars[("NoOverride", "InstallInstruct")]
  else:
    T["Instruct"] = T["NoneInstruct"]

  # Show template
  print T

  # Load any initial variables
  raise CgiUtil.JustLoggedIn, ("New install", PVars)

def Show():
  "Handle installation."

  # Make a substitution dictionary
  global Dict
  Dict = \
  {
    "Base":     os.path.abspath(os.environ["TMDA_BASE_DIR"]),
    "CryptKey": KeyGen(),
    "Home":     os.environ["HOME"],
    "Parent":   "..",
    "User":     os.environ["USER"],
    "VPop":     PVars[("NoOverride", "VPop")],
    "VPopBin":  PVars[("NoOverride", "VPopBin")]
  }

  # Load the display template
  if Form["cmd"].value == "conf-example":
    TemplateFN = "conf-example.html"
  elif Form["cmd"].value == "faq":
    TemplateFN = "faq.html"
  elif Form["cmd"].value == "install":
    Install()  # Does not return.
  elif Form["cmd"].value == "restore":
    Restore()  # Does not return.
  elif Form["cmd"].value == "uninstall":
    self[("NoOverride", "MayInstall")][0].lower() == "n":
      CgiUtil.TermError("No permission.",
        "Uninstallation disabled by sysadmin.", "uninstall",
        "", "Contact system administrator.")
    if Form.has_key("subcmd"):
      try:
        ReleaseAndDelete(int(Form["release"].value))
      except Errors.QueueError:
        pass
      Uninstall()  # Does not return.
    else:
      TemplateFN = "uninstall.html"
  elif Form["cmd"].value == "welcome":
    TemplateFN = "welcome.html"
  else:
    # Have they installed before?
    if os.access(os.path.join(os.environ["HOME"],
      PVars[("NoOverride", "UninstallBackupTGZ")]), os.R_OK):
      TemplateFN = "re-enroll.html"
    else:
      TemplateFN = "welcome.html"

  # Display template
  T = Template.Template(TemplateFN)
  print T
