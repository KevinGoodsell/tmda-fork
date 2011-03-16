import os
import shutil

rootDir = '..'
userDir = os.path.join('home', 'testuser')
filesDir = 'files'

def fixupFiles():
    '''
    Fix permissions and such that don't get saved in source control.
    '''

    os.chmod(os.path.join(userDir, '.tmda', 'crypt_key'), 0600)
    os.chmod(os.path.join(filesDir, 'test-ofmipd.auth'), 0600)

    # We need a copy of home/testuser/.tmda/config at home/testuser/config. This
    # is because tmda-ofmipd's --configdir looks for it at
    # <configdir>/<user>/config.

    shutil.copy(os.path.join(userDir, '.tmda', 'config'), userDir)
