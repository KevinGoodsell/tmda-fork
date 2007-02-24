See http://wiki.tmda.net/TmdaUpgrade for instructions on how to use
this file.

======================================================================

If you are upgrading from a release of TMDA < 1.1.11:

* the 'htdocs' directory has been removed. 

* The behavior of contrib/tofmipd.init has changed; it no longer
  auto-enables daemon startup; it is now inactive initially.

======================================================================

If you are upgrading from a release of TMDA < 1.1.8:

* The '-d/--dated' option to the 'tmda-address' command no longer
  accepts an optional timeout value.  '-d' now expects no arguments,
  and means "Generate a dated-style address using my default timeout".
  To specify a specific timeout value, use the '-t/--timeout' (which
  assumes '-d') option instead.  If you previously used '-d TIMEOUT',
  you can now get the same behavior by using '-t TIMEOUT'.  See
  'tmda-address -h' for more information.

* If you use tmda-cgi, you'll need to upgrade to at least
  tmda-cgi-0.15 to use this release of TMDA with it.

======================================================================

If you are upgrading from a release of TMDA < 1.1.6:

* The default name and location of the PENDING_CACHE file has changed
  from:

  ~/.tmda/pending/.msgcache

  to ~/.tmda/.pendingcache

  PENDING_CACHE is used by tmda-pending's '--cache' option, and also
  by tmda-cgi.  If you've set a custom value for PENDING_CACHE,
  obviously this change won't affect you, otherwise you will have to
  move the cache file to it's new location.

* Mail messages in the queue are now referred to by a unique numerical
  identifier, as discussed in TMDA/Queue/Queue.py.  For example,
  "1159383896.4198".  For most users, this change is inconsequential
  but is noted here nonetheless.

======================================================================

If you are upgrading from a release of TMDA < 1.1.4:

* contrib/sample.config has been removed in favour of the
  contrib/dot-tmda directory.

* tmda-keygen now requires that a random number device such as
  /dev/urandom be installed on the system.  Most modern Unix-like
  systems have one.  If yours does not and you can't upgrade your OS,
  you can install an add-on such as PRNGD or use
  http://tmda.net/cgi-bin/tmda-keygen

======================================================================

If you are upgrading from a release of TMDA < 1.1.3:

* The template system has been reorganized.  In particular, the
  BOUNCE_TEXT_* and CONFIRM_ACCEPT_TEXT_* configuration variables have
  been removed.  The bounce.txt template has also been removed in
  favor of multiple bounce_*.txt templates which are described in the
  TMDA template HOWTO.

  If you have not customized bounce.txt and have not set BOUNCE_TEXT_*
  and CONFIRM_ACCEPT_TEXT_* variables in your configuration, you can
  ignore this.  Otherwise, please read
  http://wiki.tmda.net/TemplateHowto for how to migrate your custom
  templates.

* Messages are now simply deleted from your pending queue once they
  are confirmed or released rather than being renamed with a '3,C' or
  '3,R' suffix.  If you are in the habit of hand-releasing pending
  messages that might be subsequently confirmed by e-mail, see the
  ACTION_MISSING_PENDING variable.

======================================================================

If you are upgrading from a release of TMDA < 1.1.1:

* ~/.tmdarc has been deprecated.  Make sure you rename this file to
  ~/.tmda/config if you are still using ~/.tmdarc.

* The TIMEOUT configuration variable has been renamed DATED_TIMEOUT.

* The Unix-style date strings in TMDA have been replaced by RFC 2822
  compatible strings in all areas of the code for easier parsing.
  You can safely ignore this unless you process these strings with
  custom scripts.

  Before: Mon Jan 19 00:13:01 MST 2004
  After:  Mon, 19 Jan 2004 00:13:01 -0700

======================================================================

If you are upgrading from a release of TMDA < 1.1.0:

* See the UPGRADE file in the latest 1.0.x point release to make sure
  you are caught up with that set of instructions.

======================================================================

^L
Local Variables:
mode: text
End:
