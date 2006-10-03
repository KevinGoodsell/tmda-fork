#!/bin/sh

# Prints the virtual email user's home directory.
#

# Expects a virtual username and the virtual domain as parameters.
# The username should be just the username portion and not the entire
# email address, e.g., if the user usually logs in as
# 'joe@example.com' or 'joe%example.com', this script should be run as
# the vpopmail user and given the parameters 'joe' and 'example.com'.
#
# $ vpopmail-vdir.sh joe example.com

# Change the following path if VPopMail's vuserinfo program is in a
# different location than given here.
VUSERINFO=~vpopmail/bin/vuserinfo

if [ -z "$2" ]
then
    vuser="$1"
else
    vuser="$1@$2"
fi

output=$(${VUSERINFO} -d "$vuser")
rc=$?

if [ $rc -ne 0 ]; then
    exit $rc
fi

set -- $output

# Older versions of vuserinfo prefaced the home directory with 'dir: '
if [ -n "$2" ]; then
    $1=$2
fi

echo $1

exit 0
