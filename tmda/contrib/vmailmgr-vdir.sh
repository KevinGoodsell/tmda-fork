#!/bin/sh

# Prints the virtual email user's home directory.
#

# Expects a virtual username and the virtual domain as parameters.
# The username should be just the username portion and not the entire
# email address, e.g., if the user usually logs in as
# 'joe@example.com' or 'joe%example.com', this script should be run as
# the system user in charge of 'example.com' (see the 'prepend' in
# /var/qmail/control/virtualdomains) and given the parameters 'joe'
# and 'example.com'.
#
# $ vmailmgr-vdir.sh joe example.com
#
# NOTE: At this point, the domain parameter ($2) is not used.

# Change the following paths if the sed program or VMailMgr's listvdomain
# program are in different locations than given here.
LISTVDOMAIN=/usr/local/bin/listvdomain
SED=/usr/bin/sed

# Set IFS to a newline (no space, no tab)
IFS='
'
output=$(${LISTVDOMAIN} $1)
rc=$?

if [ $rc -ne 0 ]; then
    exit $rc
fi

if [ ! "$output" -o -z "$output" ]; then
    exit 1
fi

set -- $output

# Reset IFS to a space, tab, newline.
IFS=' 	
'
set -- $2

# $2, now the user's home directory, is relative to $HOME and looks like this:
#
# ./users/<username>
#
# Strip off the leading dot, but leave the (now leading) '/'.
homedir=$(echo $2 | ${SED} 's/^\.//')

# No separating '/' necessary because 'homedir' begins with '/'.
echo "${HOME}${homedir}"
