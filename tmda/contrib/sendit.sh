#!/bin/sh
#
# --------------------------------------------------
#  sendit.sh    - send an email using vpopmail/tmda
#  Version      - 0.001
#  Author       - Jesse D. Guardiani
#  Created      - 01/31/03
#  Modified     - 01/31/03
# --------------------------------------------------
#  Usage: sqwebmail calls this script automatically.
#         Place this script here:
#
#         /usr/local/share/sqwebmail/sendit.sh
#
#  Note: This script ONLY works if QMail is your MTA.
#
#  ChangeLog
#  ---------
#
#  01/31/03 - JDG
#  --------------
#  - Created
# --------------------------------------------------
#
# Copyright (C) 2003 Jesse D. Guardiani <jesse@wingnet.net>
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
#
# --------------------------------------------------
# The following comments have been taken from the
# original sendit.sh that comes with sqwebmail.
# --------------------------------------------------
#
# This is a sample sendit wrapper for sqwebmail. sqwebmail will invoke this
# wrapper script to send an email message.  The complete message will be
# provided on standard input.
#
# $1 will contain the return (or bounce) address for this mailboxid, as
# specified by auth.c
#
# $2 will contain the sqwebmail mailboxid of the sender (note that we're
# executing under whatever id auth.c sets for this mailboxid).  Furthermore,
# $REMOTE_ADDR will contain the IP address where the client is coming from
# (the rest of the CGI vars are available too).
#
# The environment variable DSN will contain any requested -N option to
# sendmail (not used by qmail).
#
# You may modify the message in whatever fashion before passing it on to the
# MTA.
#
# exec /usr/sbin/sendmail -oi -t -f "$1"

PATH=~/bin 
PATH="$PATH:/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin:/usr/contrib/bin"

export PATH

# Set up some globals
TMDA_HOME=/usr/local/tmda
USERNAME=`echo "$1" | cut -f 1 -d @`
LOG_FILE_PATH='sendit.log'
DEBUG=0
WHOAMI=""


# Basic debug output function
debug_log(){
	if [ $DEBUG > 0 ]; then
		# make sure file exists
		if [ ! -f $LOG_FILE_PATH ]; then
			touch $LOG_FILE_PATH
		fi

		# write log entry
		echo "$1" >> $LOG_FILE_PATH
	fi
}

# Basic return code error message function
die_rcode() {
	EXIT_CODE=$1
	ERROR_MSG=$2

	if [ $EXIT_CODE -ne '0' ]; then
		echo "$ERROR_MSG" 1>&2
		echo "Exiting!" 1>&2
		exit "$BAD_EXIT_CODE"
	fi
}

# Determine if we are indeed running as the vpopmail user
WHOAMI=`whoami`
exit_code="$?"

die_rcode $exit_code "Error: 'whoami' call failed."

# These are the primary variables we want to keep track of
debug_log "\$DSN: $DSN \$1: $1 \$2: $2 \$WHOAMI: $WHOAMI \$USERNAME: $USERNAME"

# Vpopmail/TMDA specific code
if [ "$WHOAMI" = "vpopmail" ];then

	debug_log "attempting to run vpopmail specific code:"

	# Vpopmail specific variables
	VPOPMAIL_HOME=~vpopmail
	VUSERINFO_PATH="${VPOPMAIL_HOME}/bin/vuserinfo"
	TMDA_SENDMAIL_PATH="${TMDA_HOME}/bin/tmda-sendmail"
	VHOMEDIR=""
	
	# Get vpopmail homedir for user by sending $1 to vuserinfo
	VHOMEDIR=`${VUSERINFO_PATH} -d $1`
	exit_code="$?"

	die_rcode $exit_code "Error: 'vuserinfo' call failed."

	debug_log "  \$VHOMEDIR: $VHOMEDIR"

	# Let vpopmail know what this user's home directory is
	HOME=$VHOMEDIR
	export HOME

	# Check for TMDA
	if [ -r "${VHOMEDIR}/../.qmail-${USERNAME}" ]; then
		GREP_OUT=`grep "tmda-filter" "${VHOMEDIR}/../.qmail-${USERNAME}" | wc -l`

		debug_log "  examining 'wc' output... \$GREP_OUT=$GREP_OUT"

		# If we're piping through tmda-filter, then user must be using TMDA.
		if [ $GREP_OUT -gt 0 ]; then
			debug_log "    sending to tmda-sendmail"
			# send message through tmda
			exec $TMDA_SENDMAIL_PATH -oi  -f "$1"

			debug_log "Error: tmda-sendmail exec failed! Msg: $?"
			exit '0'
		fi
	fi
else
	debug_log "attempting to use tmda-sendmail with a non-virtual user:"
	
	# Non-virtual user TMDA code
	
	# If a .tmda directory exists, then our user probably has TMDA
	USERDIR=~${USERNAME}/

	# NOTE: This check isn't fool proof. It's just the only method I
	#       could think of at the moment.
	if [ -d "${USERDIR}.tmda" ]; then
		debug_log "    sending to tmda-sendmail"
		# send message through tmda
		exec $TMDA_SENDMAIL_PATH -oi  -f "$1"

		debug_log "Error: tmda-sendmail exec failed! Msg: $?"
		exit '0'
	fi
fi

debug_log "sending to the real sendmail"

# Well, we're still here, so send it to the 'real' sendmail.
exec /usr/sbin/sendmail -oi -t $DSN -f "$1"

debug_log "Error: 'real' sendmail exec failed! Msg: $?"
