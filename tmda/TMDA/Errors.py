# -*- python -*-

"""Shared TMDA errors and messages."""


# exception classes
class TMDAError(Exception):
    """Base class for all TMDA exceptions."""
    pass

class MissingEnvironmentVariable(TMDAError):
    """An essential environment variable is not defined."""
    def __init__(self, varname):
        TMDAError.__init__(self)
        self.varname = varname
        print 'Missing environment variable:', self.varname
