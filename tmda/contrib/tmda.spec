%define name tmda
%define version 0.57
%define release 1

Summary: Tagged Message Delivery Agent
Name: %{name}
Version: %{version}
Release: %{release}
Source0: http://software.libertine.org/tmda/releases/%{name}-%{version}.tgz
License: GPL
Group: Utilities/System
BuildRoot: /var/tmp/%{name}-buildroot
BuildArchitectures: noarch
Vendor: Jason R. Mastaler <jason@mastaler.com>
Packager: Ron Bickers <rbickers@logicetc.com>
Url: http://tmda.sourceforge.net/
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

%install
%define pyprefix %(%pypath -c 'import sys; print sys.prefix')
%define pyver %(%pypath -c 'import sys; print sys.version[:3]')
%define pylibdir %{pyprefix}/lib/python%{pyver}/site-packages
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/tmda
mkdir -p %{buildroot}%{pylibdir}/TMDA
install bin/tmda-* %{buildroot}%{_bindir}
install templates/*.txt %{buildroot}%{_datadir}/tmda
install TMDA/*.{py,pyc} %{buildroot}%{pylibdir}/TMDA

%clean
rm -rf %{buildroot}

%files
%attr(0755,root,root) %{_bindir}/*
%attr(0644,root,root) %{pylibdir}/TMDA/*.py
%verify(not size md5 mtime) %attr(0644,root,root) %{pylibdir}/TMDA/*.pyc
%attr(0644,root,root) %{_datadir}/tmda/*

%doc --parents ChangeLog COPYING CRYPTO INSTALL README THANKS UPGRADE contrib/ htdocs/{README,*.html}

%changelog

* Fri Sep 21 2001 Jason R. Mastaler <jason@mastaler.com>
  - Updated %description.

* Wed Sep 12 2001 Jason R. Mastaler <jason@mastaler.com>
  - Updated %build to call "compileall" instead of "setup".

* Wed Jun 06 2001 Ron Bickers <rbickers@logicetc.com>
  - initial RPM of TMDA 0.18
