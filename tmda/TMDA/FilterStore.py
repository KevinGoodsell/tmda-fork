# -*- python -*-
#
# Copyright (C) 2001,2002,2003 Jason R. Mastaler <jason@mastaler.com>
#
# Author: Jonathan Ellis <jonathan@carnageblender.com>
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

import os
import sys
import tempfile
##from syslog import syslog

import Util

class FlatFileStore:
    """
    Very inefficient file store.  Use only if you're too lazy
    to install any db libraries. :)
    """
    def __init__(self, name, optional):
        try:
            self.key_list = Util.file_to_list(name)
        except:
            if optional:
##                e_type, e_value = sys.exc_info()[:2]
##                syslog('could not read "%s": %s (%s)'
##                       % (name, e_type, e_value))
                self.key_list = []
            else:
                raise
                
    def contains(self, keys):
        return Util.findmatch(self.key_list, keys)


class Autobuilder:
    """
    abstract class for dbs that know how to build themselves
    from flat files.
    """
    def __init__(self, name):
        self.name = name

    # returns name of file we test against to see if build is needed
    def getReferenceFile(self):
        pass

    def build(self):
        pass

    # rebuild if basefilename is newer than the db built from it
    # returns true if successful
    def build_if_needed(self):
        try:
            txt_mtime = os.path.getmtime(self.name)
        except OSError, (e_type, e_value):
##            syslog('Could not open "%s": %s (%s)'
##                   % (self.name, e_type, e_value))
            return 0

        surrogate = self.getReferenceFile()
        # If the db doesn't exist, that's not an error.
        try:
            db_mtime = os.path.getmtime(surrogate)
        except OSError:
            db_mtime = 0

        if db_mtime <= txt_mtime:
            self.build()
            if os.path.exists(surrogate):
                mtime = time.time()
                os.utime(surrogate, (mtime, mtime))
            else:
                os.close(os.open(surrogate, os.O_CREAT, 0600))


class CdbStore(Autobuilder):
    """
    Search DJB's constant databases; see <http:/cr.yp.to/cdb.html>.
    """
    def __init__(self, name, autobuild, optional):
        if (autobuild):
            Autobuilder.__init__(self, name)
            self.build_if_needed()
            dbname = name + '.cdb'
        else:
            dbname = name
        try:
            import cdb
            self.db = cdb.init(dbname)
        except:
            if optional:
##                e_type, e_value = sys.exc_info()[:2]
##                syslog('could not read "%s": %s (%s)'
##                       % (name, e_type, e_value))
                self.db = None
            else:
                raise

    def contains(self, keys):
        if self.db != None:
            for key in keys:
                if key and self.db.has_key(key.lower()):
                    return 1
        return 0

    def getReferenceFile(self):
        return self.name + '.cdb'

    def build(self):
        import cdb
        # allow exceptions to propagate up to getStore
        dbname = self.name + '.cdb'
        tempfile.tempdir = os.path.dirname(self.name)
        tmpname = os.path.split(tempfile.mktemp())[1]
        cdb = cdb.cdbmake(dbname, dbname + '.' + tmpname)
        for line in file_to_list(self.name):
            linef = line.split()
            key = linef[0].lower()
            try:
                value = linef[1]
            except IndexError:
                value = ''
            cdb.add(key, value)
        cdb.finish()


class DbmStore(Autobuilder):
    """
    Search a DBM-style database.
    """
    
    def __init__(self, name, autobuild, optional):
        if (autobuild):
            Autobuilder.__init__(self, name)
            self.build_if_needed()
            dbname = name + '.db'
        else:
            dbname = name
        try:
            import anydbm
            self.db = anydbm.open(dbname, 'r')
        except:
            if optional:
##                e_type, e_value = sys.exc_info()[:2]
##                syslog('could not read "%s": %s (%s)'
##                       % (name, e_type, e_value))
                self.db = None
            else:
                raise

    def contains(self, keys):
        if self.db != None:
            for key in keys:
                if key and self.db.has_key(key.lower()):
                    return 1
        return 0

    # we don't know exactly what the actual db file is, so we
    # test against this instead:
    def getReferenceFile(self):
        return self.name + '.last_built'

    def build(self):
        # allow exceptions to propagate up to getStore
        import anydbm
        import glob
        dbmpath, dbmname = os.path.split(self.name)
        dbmname += '.db'
        tempfile.tempdir = dbmpath
        tmpname = tempfile.mktemp()
        dbm = anydbm.open(tmpname, 'n')
        for line in Util.file_to_list(self.name):
            linef = line.split()
            key = linef[0].lower()
            try:
                value = linef[1]
            except IndexError:
                value = ''
            dbm[key] = value
        dbm.close()
        # Tim Legant says:
        # Only the filename string returned from tempfile.mktemp is
        # known on all platforms.  The extension cannot be assumed.
        # Additionally, on some platforms, a call to create a new database
        # actually creates more than one file.  I believe this is true on
        # Solaris, for instance.  Often the second file is an index file.
        for f in glob.glob(tmpname + '*'):
            (tmppath, tmpname) = os.path.split(tmpname)
            newf = f.replace(tmpname, dbmname)
            newf = os.path.join(tmppath, newf)
            os.rename(f, newf)


class EzmlmStore:
    """ ezmlm subscriber directories """

    def __init__(self, name, optional):
        self.ezmlm_list = []
        dir = os.path.join(name, 'subscribers')
        # See ezmlm(5) for dir/subscribers format.
        try:
            for file in os.listdir(dir):
                fp = open(os.path.join(dir, file), 'r')
                subs = fp.read().split('\x00')
                for sub in subs:
                    if sub:
                        self.ezmlm_list.append(sub.split('T', 1)[1].lower())
        except:
            if optional:
##                e_type, e_value = sys.exc_info()[:2]
##                syslog('could not read "%s": %s (%s)'
##                       % (name, e_type, e_value))
                self.keys = []
            else:
                raise
        
    def contains(self, keys):
        for key in keys:
            if key and key.lower() in self.ezmlm_list:
                return 1
        return 0


class MailmanStore:
    """
    Mailman configuration databases
    (note that this init takes a 2nd arg)
    """
    
    def __init__(self, name, mmkey, optional):
        # Find the Mailman configuration database.
        # 'config.db' is a Python marshal used in MM 2.0, and
        # 'config.pck' is a Python pickle used in MM 2.1.
        config_db = os.path.join(name, 'config.db')
        config_pck = os.path.join(name, 'config.pck')
        if os.path.contains(config_pck):
            dbfile = config_pck
            import cPickle as Serializer
        elif os.path.contains(config_db):
            dbfile = config_db
            import marshal as Serializer
        else:
##            syslog('could not read mailman config database')
            self.mmdb_list = []
            return

        try:
            mmdb_file = open(dbfile, 'r')
            mmdb_data = Serializer.load(mmdb_file)
            mmdb_file.close()
            self.mmdb_list = mmdb_data[mmdb_key]

            # Make sure self.mmdb_list is a list of e-mail addresses.
            if type(self.mmdb_list) is types.DictType:
                self.mmdb_list = mmdb_data[mmdb_key].keys()
        except:
            if optional:
##                e_type, e_value = sys.exc_info()[:2]
##                syslog('could not read "%s": %s (%s)'
##                       % (name, e_type, e_value))
                self.mmdb_list = []
            else:
                raise

    def contains(self, keys):
        for addr in keys:
            if addr and addr.lower() in self.mmdb_list:
                return 1
        return 0


def getStore(type, name, args):
    name = os.path.expanduser(name)
    optional = args.has_key('optional')
    
    # 'from-file' or 'to-file', including autocdb functionality
    if type in ('from-file', 'to-file'):
        if args.has_key('autocdb'):
            try:
                return CdbStore(name, 1, optional)
            except:
                pass
##                e_type, e_value = sys.exc_info()[:2]
##                syslog('could not autobuild cdb for "%s": %s (%s)'
##                       % (name, e_type, e_value))
        elif args.has_key('autodbm'):
            try:
                return DbmStore(name, 1, optional)
            except:
                pass
##                e_type, e_value = sys.exc_info()[:2]
##                syslog('could not autobuild dbm for "%s": %s (%s)'
##                       % (name, e_type, e_value))
        # db types fall through to here on failure -- 
        # we'll try flatfile, in case the problem was with the db
        return FlatFileStore(name, optional)

    if type in ('from-dbm', 'to-dbm'):
        return DbmStore(name, optional)

    if type in ('from-cdb', 'to-cdb'):
        return CdbStore(name, optional)

    if type in ('from-ezmlm', 'to-ezmlm'):
        return EzmlmStore(name, optional)

    if type in ('from-mailman', 'to-mailman'):
        try:
            mmdb_key = args['attr']
        except KeyError:
            raise NameError(lineno,
                             '"%s" missing -attr argument' % type)
        return MailmanStore(name, mmdb_key, optional)

    return None
