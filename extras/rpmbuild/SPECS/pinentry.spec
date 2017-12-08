Summary: Collection of simple PIN or passphrase entry dialogs
Name:    pinentry
Version: 1.0.0
Release: 1%{?dist}
License: GPLv2+
URL:     http://www.gnupg.org/aegypten/
Source0: ftp://ftp.gnupg.org/gcrypt/pinentry/%{name}-%{version}.tar.bz2
Source1: ftp://ftp.gnupg.org/gcrypt/pinentry/%{name}-%{version}.tar.bz2.sig
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: ncurses
Provides: %{name}-curses = %{version}-%{release}
Provides: %{name}-tty = %{version}-%{release}

%description
Pinentry is a collection of simple PIN or passphrase entry dialogs which
utilize the Assuan protocol as described by the aegypten project; see
http://www.gnupg.org/aegypten/ for details.
This package contains the curses (text) based version of the PIN entry dialog.

%prep
%setup -q

%build
%configure \
  --disable-rpath \
  --disable-dependency-tracking \
  --without-libcap \
  --enable-pinentry-curses \
  --enable-pinentry-tty \
  --disable-pinentry-gnome3 \
  --disable-pinentry-gtk2 \
  --disable-pinentry-qt5 \
  --disable-pinentry-emacs
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
rm -f %{buildroot}/%{_libdir}/*.la %{buildroot}/%{_infodir}/dir

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%{!?_licensedir:%global license %%doc}
%license COPYING
#%doc AUTHORS ChangeLog NEWS README THANKS TODO
%{_prefix}/*

%changelog
* Sun Nov 12 2017 Local EGA build - Frédéric Haziza <daz@nbis.se> - 1.27
- Building for the ingestion worker docker image


