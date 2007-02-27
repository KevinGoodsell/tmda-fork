NOTE: Recent versions of tmda-ofmipd contain native support for SSL. As such,
this "HOWTO" is probably not relevant any more, unless you have some specific
requirement to use stunnel.


The files in this directory show how to run a daemonized stunnel to provide
TLS encrypted connections to a daemonized tmda-ofmipd.

NOTE: One issue with this approach is that tmda-ofmipd sees all connections as
originating from the machine where stunnel is running, typically localhost.
This may or may-not be an issue for you. Note that this client IP address is
added into the email headers by tmda-ofmipd.

It is assumed that tmda-ofmipd is already running as a daemon.

The files are:

stunnel.conf:
  Add the content of this file to your existing stunnel.conf, and start,
  or restart, the stunnel daemon.

