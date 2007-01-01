The files in this directory show how to run tmda-ofmipd from xinet.d, using
stunnel to provide TLS encryption.

The same general principles (i.e. tmda-ofmipd "one-session" mode) should allow
running tmda-ofmipd under DJB's tcpserver. A previous version of this patch
was developed for this situation, so it should work fine.

The files are:

xinetd.d-tmda-ofmipd-starttls

    Put this in /etc/xinet.d/tmda-ofmipd-starttls. This file configures xinetd
    to listen for connections, and run the stunnel wrapper script for each
    connection. You will need an entry such as the following in /etc/services:

    tmda-ofmipd-starttls 8026/tcp

stunnel-wrapper

    xinetd runs this script for each connection. This script invokes stunnel
    using stunnel.conf

stunnel.conf

    This configuration file tells stunnel what to do with the connection;
    specifically, setup an SMTP session, allow STARTTLS, and then invoke
    tmda-ofmipd in one-session mode

    NOTE: I personally store both the server certificate and private key in
    the same file (hence the extension .key-and-crt). If you do not do this,
    then you will need to replace the "cert =" line in stunnel.conf with
    something along these lines:

        cert = /etc/ssl/keys/severn.wwwdotorg.org.crt
        key  = /etc/ssl/keys/severn.wwwdotorg.org.key

tmda-ofmipd-wrapper

    Once stunnel has established the TLS-encrypted SMTP session, it runs this
    script to actually communicate with the SMTP client. This script invokes
    tmda-ofmipd in "one-session" mode, and appropriate authentication etc.
    options.

