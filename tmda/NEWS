This file contains a list of new features and capabilities by TMDA
version.  These blurbs are what are usually included in release
announcements under "What's new?".  Make sure to read the UPGRADE
file in this directory as well.

======================================================================

TMDA 1.1.12 "Macallan" --

* tmda-ofmipd now has native STARTTLS and SSL support courtesy of
  Stephen Warren. The new options are '--tls', '--ssl', '--ssl-key',
  and '--ssl-crt'. Note that the tlslite Python module needs to be
  installed to use this feature. For more information, see the
  "Builtin SSL/TLS" section of http://wiki.tmda.net/TmdaOfmipdHowto

* Fixed a minor bug that prevented the use of both SMTPSSL and
  SMTPAUTH together.

======================================================================

TMDA 1.1.11 "Ladyburn" --

* The snapshot of the wiki documentation is now included within the
  main tmda-1.1.x.tgz tarball in the 'doc' directory rather than in a
  separate tmda-1.1.x-doc.tgz tarball.

* New feature courtesy of Vitor Espindola. A new configuration
  variable, TIMEOUT_UNITS, to give users the ability to customize the
  timeout unit value strings in the templates instead of using the
  English defaults of "years", "months", "weeks", "days", "hours",
  "minutes", and "seconds". For more information, see
  http://wiki.tmda.net/ConfigurationVariables#TIMEOUT_UNITS

* Virtual domain improvements to tmda-pending courtesy of Lloyd
  Zusman. A '--vhost-script' command-line option has been added to
  match tmda-ofmipd and tmda-filter. Also two new options have been
  added, '--vhost-user' and '--vhost-domain'. See the tmda-pending
  --help output for more information, or for greater detail, see
  http://article.gmane.org/gmane.mail.spam.tmda.devel/6584

* An alternative "simpler" example of how to use TLS with tmda-ofmipd
  via stunnel has been added. See the contrib/ofmipd-stunnel-daemons/
  directory.

* A bug that broke tmda-filter's '-e' command-line option has been
  fixed.

* A 'reload' option has been added to contrib/tofmipd.init, just for
  correctness; it currently does the same thing as 'restart'.

======================================================================

TMDA 1.1.10 "Killyloch" --

* New feature. When a message is released from your pending queue via
  tmda-cgi, a new trace header 'X-TMDA-CGI' is added to the message
  which contains both the IP address of the remote host as well as the
  browser the client used to send the request.  This allows you to
  visually discern that the message was released via tmda-cgi rather
  than through email confirmation, and also allows for easier tracing.

* tmda-ofmipd has a new option courtesy of Robert P. Thille.  `-L'
  turns on logging prints which logs everything that `-d' logs, except
  for the raw SMTP protocol data. Hence, it is useful if you want to
  leave logging enabled permanently, but don't want your logs bloated
  with AUTH data and/or the content of large attachments.

* tmda-ofmipd bugfixes and improvements from Stephen Warren.

======================================================================

TMDA 1.1.9 "Jura" --

* New feature courtesy of Mark Horn. ACTION_EXPIRED_DATED has been
  extended to support handling multiple ages of dated messages. So you
  could for example 'bounce' mail to dated addresses that have been
  expired for more than a week, 'hold' if longer than a month, and
  'drop' if over a year, while still setting the default behavior to
  'confirm'.  For more information and an illustrative example, see
  http://wiki.tmda.net/ConfigurationVariables#ACTION_EXPIRED_DATED

======================================================================

TMDA 1.1.8 "Imperial" --

* TMDA's internal copy of the Python email package has been upgraded
  to v4.0.1.

* The bin/tmda-* programs have been revamped to use Python's new
  'optparse' library.

======================================================================

TMDA 1.1.7 "Hazelburn" --

* TMDA can now optionally store unconfirmed messages in a "Maildir"
  rather than in TMDA's custom pending queue format.  This allows you
  to use any mail reading program that supports Maildir to browse or
  search your pending queue, rather than the 'tmda-pending' and
  'tmda-cgi' programs, though the latter will still work.

  For more infomation on how to enable and use this feature, please
  see http://wiki.tmda.net/TmdaPendingAsMaildir

* tmda-filter has a new command-line option, '-e/--environ' which you
  can use to add a VAR=value pair to the environment.  One example use
  of this is to allow TMDA to be setup as a Postfix transport.
  Contributed by Bernard Johnson.

======================================================================

TMDA 1.1.6 "Glen Albyn" --

* tmda-filter will defer incoming deliveries if the sticky bit is set
  on your home directory (as determined by the $HOME variable).  This
  allows you to safely edit the contents of ~/.tmda/ on a live system
  if you need to.  Set the sticky bit with:

  % chmod +t $HOME

  And make sure to remove it when you are done (chmod -t $HOME).  This
  idea comes from qmail-local.  See "SAFE QMAIL EDITING" at
  http://www.qmail.org/man/man5/dot-qmail.html

* tmda-ofmipd now has "one-session" mode through the '--one-session'
  command-line option, courtesy of Stephen Warren.  This allows you to
  use xinetd or tcpserver, possibly in conjunction with stunnel, to
  spawn tmda-ofmipd, rather than having tmda-ofmipd bind to a port and
  accept connections on its own.

  This allows you to re-use your existing xinetd/tcpserver
  configuration/management and access control rules.  It also allows
  tmda-ofmipd to see the real IP address of the client, for better
  Received: line logging.

  See the contrib/ofmipd-stunnel-xinetd directory for a README and
  some configuration examples.

======================================================================

TMDA 1.1.4 "Edradour" --

* The new 'dot-tmda' directory in contrib contains a working ~/.tmda/
  structure that can be used with only a few changes.  See the README
  in that directory for more info.  Not documented yet outside of the
  README, but this might help new TMDA users get started quicker.

* Some of the tmda-* programs will now run on native win32
  (tmda-address, tmda-check-address, tmda-pending, and tmda-keygen).

* tmda-ofmipd has a new option (--pure-proxy) that can proxy mail for
  non-TMDA users in addition to TMDA users.  This might be useful if
  you run a mixed environment, and want to use tmda-ofmipd for
  everyone.  See `tmda-ofmipd --help' for more on this option.

======================================================================

TMDA 1.1.3 "Dailuaine" --

* New feature from David Bremner.  Add 'shell=' and 'python=' tag
  actions to the outgoing filter.  This allows you to add
  dynamic/shell escaped headers from the outgoing filter file.  For
  example usage, see the TMDA/Hashcash HOWTO I've prepared at
  http://wiki.tmda.net/TmdaHashCashHowto

* The template system has been reorganized to simplify things for
  users of multi-lingual templates among others.  See
  http://wiki.tmda.net/TemplateHowto and the UPGRADE notes below.

* Messages are now simply deleted from your pending queue once they
  are confirmed or released rather than being renamed with a '3,C' or
  '3,R' suffix.  This provides simpler, more intuitive behavior and
  decreased storage requirements.

======================================================================

TMDA 1.1.2 "Caol Ila" --

* Fixed a bug in TMDAINJECT that caused Message-ID and Date headers to
  differ when sending to multiple recipients.

* Fixes to the tmda.spec file that should allow RPMs to be built with
  Python 2.3.x.

======================================================================

TMDA 1.1.1 "Balblair" --

* Tilde expansion is now done automatically for variables in
  /etc/tmdarc and ~/.tmda/config, so you no longer have to use
  os.path.expanduser() to do this yourself.  e.g,

  TEMPLATE_DIR = "~/.tmda/templates"

  now ``just works''.

* New 'whitelist' behavior for tmda-pending and tmda-cgi, controlled
  by http://wiki.tmda.net/ConfigurationVariables#PENDING_WHITELIST_RELEASE

* A new 'pipe-headers' incoming filter file source.  Identical to
  'pipe' except that it only pipes the headers to the program, instead
  of the headers + body.  This should offer greater performance and
  reliability when processing the message body isn't required.

* A new feature to add Mail-Followup-To headers from tmda-sendmail or
  tmda-ofmipd to messages.  See
  http://wiki.tmda.net/ConfigurationVariables#MAIL_FOLLOWUP_TO

======================================================================

^L
Local Variables:
mode: text
End:
