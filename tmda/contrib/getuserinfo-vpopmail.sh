#!/bin/sh

# Prints the virtual email user's home directory on line 1,
# the user's UID on line 2, and the user's GID on line 3.
#

# Expects a virtual username and the virtual domain as parameters.
# The username should be just the username portion and not the entire
# email address, e.g., if the user usually logs in as
# 'joe@example.com' or 'joe%example.com', this script should be run as
# the vpopmail user and given the parameters 'joe' and 'example.com'.
#
# $ getuserinfo-vpopmail.sh joe example.com



# dieifbadexit() is used to provide a uniform way to display an error
# and exit with 1 if the last command executed had a -gt 0 exit status.
# argument 1 is the last command's exit status, and argument 2 is the
# message to print if argument 1 is -gt 0.
dieifbadexit( ) {
	if [ "$1" -ne 0 ]; then
		echo "$2"
		exit 1
	fi
}

# Change the following path if VPopMail's vuserinfo program is in a
# different location than given here.
VUSERINFO=~vpopmail/bin/vuserinfo

if [ -z "$2" ]
then
    vuser="$1"
else
    vuser="$1@$2"
fi

# ----------------------------------------------------
# print user dir, minus any preceding "dir: " garbage.
# ----------------------------------------------------
DIR=`${VUSERINFO} -d $vuser`
# Catch any bad exit status
dieifbadexit "$?" "Error: Virtual User Dir retrieval failed! $DIR"
# Filter out garbage
echo "$DIR" | sed 's/^dir:[[:space:]]*//'
# Catch any bad exit status
dieifbadexit "$?" "Error: Virtual User Dir filtering failed!"

# ----------------------------------------------------
# print UID
# ----------------------------------------------------
${VUSERINFO} -u $vuser
# Catch any bad exit status
dieifbadexit "$?" "Error: Virtual User UID retrieval failed!"



# ----------------------------------------------------
# print GID
# ----------------------------------------------------
IFS=
GID=`${VUSERINFO} -g $vuser`
# Catch any bad exit status
dieifbadexit "$?" "Error: Virtual User GID retrieval failed!"

echo "$GID" | sed '2,$d'
# Catch any bad exit status
dieifbadexit "$?" "Error: Virtual User GID filtering failed!"

unset IFS
