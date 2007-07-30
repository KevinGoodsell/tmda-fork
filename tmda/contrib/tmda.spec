%define name tmda
%define version 1.1.12
%define release 1

Summary: Tagged Message Delivery Agent
Name: %{name}
Version: %{version}
Release: %{release}
Source0: http://tmda.net/releases/%{name}-%{version}.tgz
License: GPL
Group: Utilities/System
BuildRoot: %{_tmppath}/%{name}-buildroot
BuildArchitectures: noarch
Vendor: TMDA Cabal
Packager: tmda-workers@tmda.net
Url: http://tmda.net/
BuildRequires: /usr/bin/python2.3
Requires: /usr/bin/python2.3

%description
TMDA is an open source anti-spam system and local mail delivery agent.

%prep
%setup -q

%build
rm -rf %{buildroot}
#%define pypath %(if [ `type -p python2` ]; then type -p python2; else type -p python; fi)
%define pypath /usr/bin/python2.3

# fix shbang line in all executable files
find . -type f -perm 0755 -print | while read i
do
  sed '1,1s|/usr/bin/env python|%pypath|g' $i > $i.tmp && mv $i.tmp $i && chmod 0755 $i
done

%pypath ./compileall

%install
%define pyprefix %(%pypath -c 'import sys; print sys.prefix')
%define pyver %(%pypath -c 'import sys; print sys.version[:3]')
%define pylibdir %{pyprefix}/lib/python%{pyver}/site-packages
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/tmda
mkdir -p %{buildroot}%{_datadir}/emacs/site-lisp
mkdir -p %{buildroot}%{pylibdir}/TMDA/{Queue,pythonlib/email/mime}
mkdir -p %{buildroot}%{_sysconfdir}/{rc.d/init.d,sysconfig}
install bin/tmda-* %{buildroot}%{_bindir}
install templates/*.txt %{buildroot}%{_datadir}/tmda
install TMDA/*.{py,pyc} %{buildroot}%{pylibdir}/TMDA
install TMDA/Queue/*.{py,pyc} %{buildroot}%{pylibdir}/TMDA/Queue
install TMDA/pythonlib/email/*.{py,pyc} %{buildroot}%{pylibdir}/TMDA/pythonlib/email
install TMDA/pythonlib/email/mime/*.{py,pyc} %{buildroot}%{pylibdir}/TMDA/pythonlib/email/mime
install contrib/print{cdb,dbm} %{buildroot}%{_bindir}
install contrib/collectaddys %{buildroot}%{_bindir}
install contrib/tmda.el %{buildroot}%{_datadir}/emacs/site-lisp
install contrib/tofmipd.init %{buildroot}%{_sysconfdir}/rc.d/init.d/tofmipd
install contrib/tofmipd.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/tofmipd

%clean
rm -rf %{buildroot}

%files
%defattr(0644,root,root)
%attr(0755,root,root) %{_bindir}/*
%{pylibdir}/TMDA/*.py
%{pylibdir}/TMDA/Queue/*.py
%{pylibdir}/TMDA/pythonlib/email/*.py
%{pylibdir}/TMDA/pythonlib/email/mime/*.py
%verify(not size md5 mtime) %{pylibdir}/TMDA/*.pyc
%verify(not size md5 mtime) %{pylibdir}/TMDA/Queue/*.pyc
%verify(not size md5 mtime) %{pylibdir}/TMDA/pythonlib/email/*.pyc
%verify(not size md5 mtime) %{pylibdir}/TMDA/pythonlib/email/mime/*.pyc
%{_datadir}/tmda/*

%doc --parents ChangeLog CODENAMES COPYING CRYPTO INSTALL NEWS README THANKS UPGRADE contrib/ doc/

%package ofmipd
Summary: Tagged Message Delivery Agent - ofmipd server
Group: System/Daemons
Requires: tmda >= %{version}
Url: http://wiki.tmda.net/TmdaOfmipdHowto
%description ofmipd
tmda-ofmipd is an async I/O based authenticated ofmip proxy for TMDA.
This allows users of any mail client capable of SMTP Authentication
to "tag" their outgoing mail in the TMDA-style.

%files ofmipd
%defattr(0644,root,root)
%attr(0755,root,root) %{_bindir}/tmda-ofmipd
%attr(0755,root,root) %{_sysconfdir}/rc.d/init.d/tofmipd
%config(noreplace) %{_sysconfdir}/sysconfig/tofmipd

%pre ofmipd
/usr/sbin/groupadd -r tofmipd >/dev/null 2>&1 || :
/usr/sbin/useradd -r -g tofmipd -d /var/tmp -s /dev/null tofmipd >/dev/null 2>&1 || :

%post ofmipd
chkconfig --add tofmipd
service tofmipd start > /dev/null 2>&1 || :

%preun ofmipd
service tofmipd stop > /dev/null 2>&1 || :
chkconfig --del tofmipd

%postun ofmipd
# The friendly thing seems to be leave users hanging around
#/usr/sbin/userdel ofmipd >/dev/null 2>&1 || :
#/usr/sbin/groupdel ofmipd >/dev/null 2>&1 || :

%package emacs
Summary: Tagged Message Deliver Agent - Emacs Support Files
Group: Utilities/System
Requires: tmda >= %{version}, emacs
%description emacs
This module contains useful helper routines for using TMDA from
Gnus (and perhaps other Emacs based mail/news readers). 

%files emacs
%defattr(0644,root,root)
%{_datadir}/emacs/site-lisp/tmda.el

%changelog

* Mon Feb  9 2004 Jason R. Mastaler <jason@mastaler.com>
  - version 1.1.x start

* Fri Dec 19 2003 Jason R. Mastaler <jason@mastaler.com> 1.0-1
  - version 1.0 release

* Fri Apr 25 2003 Bernard Johnson <bjohnson@symetrix.com>
  - version 0.76, remove tmda-cgi subpackage (it's not a part of TMDA anymore)
    and remove the multi-arch build it required

* Sun Dec 01 2002 Bernard Johnson <bjohnson@symetrix.com>
  - version 0.66, repackaged for subpackages, builds multiple archs

* Wed Jun 06 2001 Ron Bickers <rbickers@logicetc.com>
  - initial RPM of TMDA 0.18
