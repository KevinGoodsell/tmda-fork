%define name tmda
%define version 0.21
%define release 1

Summary: Tagged Message Delivery Agent
Name: %{name}
Version: %{version}
Release: %{release}
Source0: http://prdownloads.sourceforge.net/tmda/%{name}-%{version}.tgz
License: BSD
Group: Utilities/System
BuildRoot: /var/tmp/%{name}-buildroot
BuildArchitectures: noarch
Vendor: Jason R. Mastaler <jason@mastaler.com>
Packager: Ron Bickers <rbickers@logicetc.com>
Url: http://tmda.sourceforge.net/

%description
TMDA is an OSI certified software application designed to significantly
reduce (or eliminate) the amount of SPAM/UCE you receive by using unique,
cryptographically enhanced (tagged) e-mail addresses. TMDA can both filter
your incoming e-mail, and tag your outgoing address.

%prep
%setup

%build
python ./setup

%install
%define pyprefix %(python -c 'import sys; print sys.prefix')
%define pyver %(python -c 'import sys; print sys.version[:3]')
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

%doc ChangeLog COPYRIGHT CRYPTO FAQ INSTALL README THANKS TODO UPGRADE contrib/ doc/

%changelog

* Wed Jun 06 2001 Ron Bickers <rbickers@logicetc.com>
  - initial RPM of TMDA 0.18
