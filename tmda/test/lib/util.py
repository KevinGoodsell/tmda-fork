import os
import shutil
import sys

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

def fixupPythonPath():
    sys.path.append(rootDir)

def fixupHome():
    os.environ['HOME'] = userDir

def testPrep():
    fixupFiles()
    fixupHome()
    fixupPythonPath()

# Used to generate "bad" usernames and passwords.
def wordVariants(word):
    variants = []

    variants.append(word[1:])                     # estuser
    variants.append(word[:-1])                    # testuse
    variants.append(word[0] + word)               # ttestuser
    variants.append(word + word[-1])              # testuserr
    variants.append(word[0] + word[1] + word[1:]) # teestuser
    variants.append(word[0] + word[2] + word[2:]) # tsstuser
    variants.append(word[1] + word[0] + word[2:]) # etstuser

    # Some unexpected prefixes
    variants.append(' ' + word)
    variants.append('\x00' + word)

    # Possible problem strings
    variants.append('')
    variants.append(' ')
    variants.append('\x00')

    return variants

def badUsersPasswords(username, password):
    '''Generate incorrect (username, password) pairs based on username and
    password'''
    pairs = []

    for badPass in wordVariants(password):
        pairs.append((username, badPass))

    for badUser in wordVariants(username):
        pairs.append((badUser.strip(), password))

    result = []
    for pair in pairs:
        if pair == (username, password) or pair in result:
            continue

        result.append(pair)

    return result
