%define name tmda
%define version 0.66
%define release 1

Summary: Tagged Message Delivery Agent
Name: %{name}
Version: %{version}
Release: %{release}
Source0: http://tmda.net/releases/%{name}-%{version}.tgz
Source1: ofmipd.init
Source2: ofmipd.sysconfig
Source3: ofmipd.passwd
Source4: tmda-cgi.conf
License: GPL
Group: Utilities/System
BuildRoot: %{_tmppath}/%{name}-buildroot
BuildArchitectures: noarch
Vendor: Jason R. Mastaler <jason@mastaler.com>
Packager: tmda-workers@tmda.net
Url: http://tmda.net/
BuildRequires: /usr/bin/python2
Requires: /usr/bin/python2

%description
TMDA is an OSI certified software application designed to
significantly reduce the amount of SPAM/UCE (junk-mail) you receive.
TMDA combines a "whitelist" (for known/trusted senders), a "blacklist"
(for undesired senders), and a cryptographically enhanced confirmation
system (for unknown, but legitimate senders).


%prep
%setup

%build
%define pypath %(if [ `type -p python2` ]; then type -p python2; else type -p python; fi)

# fix shbang line in all executable files
find . -type f -perm 0755 -print | while read i
do
  sed '1,1s|/usr/bin/env python|%pypath|g' $i > $i.tmp && mv $i.tmp $i && chmod 0755 $i
done

%pypath ./compileall
pushd contrib/cgi
%pypath ./compile

%install
%define pyprefix %(%pypath -c 'import sys; print sys.prefix')
%define pyver %(%pypath -c 'import sys; print sys.version[:3]')
%define pylibdir %{pyprefix}/lib/python%{pyver}/site-packages
%define cgidir %{pylibdir}/TMDA/cgi
%define httpdconfdir %{_sysconfdir}/httpd/conf.d
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_sbindir}
mkdir -p %{buildroot}%{_datadir}/tmda
mkdir -p %{buildroot}%{_datadir}/emacs/site-lisp
mkdir -p %{buildroot}%{pylibdir}/TMDA/pythonlib/email
mkdir -p %{buildroot}%{cgidir}/display
mkdir -p %{buildroot}%{_sysconfdir}/{rc.d/init.d,sysconfig}
mkdir -p %{buildroot}%{httpdconfdir}
install bin/tmda-* %{buildroot}%{_bindir}
rm -f %{buildroot}%{_bindir}/tmda-ofmipd
install bin/tmda-ofmipd %{buildroot}%{_sbindir}
install templates/*.txt %{buildroot}%{_datadir}/tmda
install TMDA/*.{py,pyc} %{buildroot}%{pylibdir}/TMDA
install TMDA/pythonlib/email/*.{py,pyc} %{buildroot}%{pylibdir}/TMDA/pythonlib/email
install contrib/print{cdb,dbm} %{buildroot}%{_bindir}
install contrib/collectaddys %{buildroot}%{_bindir}
install contrib/tmda.el %{buildroot}%{_datadir}/emacs/site-lisp
install contrib/cgi/*.{py,pyc} %{buildroot}%{cgidir}
install contrib/cgi/tmda-cgi %{buildroot}%{cgidir}/tmda.cgi
install contrib/cgi/display/*.{gif,css} %{buildroot}%{cgidir}/display
install %SOURCE1 %{buildroot}%{_sysconfdir}/rc.d/init.d/ofmipd
install %SOURCE2 %{buildroot}%{_sysconfdir}/sysconfig/ofmipd
install %SOURCE3 %{buildroot}%{_sysconfdir}/ofmipd
cat %SOURCE4 | sed -e 's|SITE_DIR|%{cgidir}|' > %{buildroot}%{httpdconfdir}/tmda.conf
ln -s %{_bindir}/tmda-inject %{buildroot}%{_sbindir} 

%clean
rm -rf %{buildroot}

%files
%attr(0755,root,root) %{_bindir}/*
%attr(0644,root,root) %{pylibdir}/TMDA/*.py
%attr(0644,root,root) %{pylibdir}/TMDA/pythonlib/email/*.py
%verify(not size md5 mtime) %attr(0644,root,root) %{pylibdir}/TMDA/*.pyc
%verify(not size md5 mtime) %attr(0644,root,root) %{pylibdir}/TMDA/pythonlib/email/*.pyc
%attr(0644,root,root) %{_datadir}/tmda/*

%doc --parents ChangeLog CODENAMES COPYING CRYPTO INSTALL README THANKS UPGRADE contrib/ htdocs/{README,*.html}

%package ofmipd
Summary: Tagged Message Delivery Agent - ofmipd server
Group: System/Daemons
Requires: tmda >= %{version}
%description ofmipd
TMDA is an OSI certified software application designed to
significantly reduce the amount of SPAM/UCE (junk-mail) you receive.
This subpackage is the ofmipd server.

%files ofmipd
%attr(0755,root,root) %{_sbindir}/tmda-ofmipd
%attr(0755,root,root) %{_sysconfdir}/rc.d/init.d/ofmipd
%attr(0755,root,root) %{_sysconfdir}/ofmipd
%{_sbindir}/tmda-inject
%config %attr(0644,root,root) %{_sysconfdir}/sysconfig/ofmipd

%pre ofmipd
/usr/sbin/groupadd -r ofmipd >/dev/null 2>&1 || :
/usr/sbin/useradd -r -g ofmipd -d /var/tmp -s /dev/null ofmipd >/dev/null 2>&1 || :

%post ofmipd
chkconfig --add ofmipd

%preun ofmipd
service ofmipd stop > /dev/null 2>&1 || :
chkconfig --del ofmipd

%postun ofmipd
/usr/sbin/userdel ofmipd >/dev/null 2>&1 || :
/usr/sbin/groupdel ofmipd >/dev/null 2>&1 || :

%package cgi
Summary: Tagged Message Delivery Agent - CGI Interface
Group: Utilities/System
Requires: tmda >= %{version}, httpd
%description cgi
TMDA is an OSI certified software application designed to
significantly reduce the amount of SPAM/UCE (junk-mail) you receive.
This subpackage is the CGI interface to TMDA.

%files cgi
%attr(0644,root,root) %{cgidir}/*.py
%verify(not size md5 mtime) %attr(0644,root,root) %{cgidir}/*.pyc
%attr(4755,root,root) %{cgidir}/tmda.cgi
%attr(0644,root,root) %{cgidir}/display/*
%attr(0644,root,root) %{httpdconfdir}/tmda.conf
%doc contrib/cgi/README

%post cgi
service httpd reload

%preun cgi
service httpd reload

%package emacs
Summary: Tagged Message Deliver Agent - Emacs Support Files
Group: Utilities/System
Requires: tmda >= %{version}, emacs
%description emacs
TMDA is an OSI certified software application designed to
significantly reduce the amount of SPAM/UCE (junk-mail) you receive.
This subpackage is the emacs support files for TMDA.

%files emacs
%attr(0644,root,root) %{_datadir}/emacs/site-lisp/tmda.el

%changelog
* Sun Dec 01 2002 Bernard Johnson <bjohnson@symetrix.com>
  - version 0.66

* Wed Jun 06 2001 Ron Bickers <rbickers@logicetc.com>
  - initial RPM of TMDA 0.18
