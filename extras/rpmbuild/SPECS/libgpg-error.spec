Summary: Library for error values used by GnuPG components
Name: libgpg-error
Version: 1.27
Release: 1%{?dist}
Source0: ftp://ftp.gnupg.org/gcrypt/libgpg-error/%{name}-%{version}.tar.bz2
Source1: ftp://ftp.gnupg.org/gcrypt/libgpg-error/%{name}-%{version}.tar.bz2.sig
Group: System Environment/Libraries
License: LGPLv2+
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: gawk, gettext, autoconf, automake, gettext-devel, libtool

%description
This is a library that defines common error values for all GnuPG
components.  Among these are GPG, GPGSM, GPGME, GPG-Agent, libgcrypt,
pinentry, SmartCard Daemon and possibly more in the future.

%prep
%setup -q

%build
%configure --disable-static \
	   --disable-rpath \
	   --disable-languages \
	   --disable-doc
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
rm -f %{buildroot}/%{_libdir}/*.la %{buildroot}/%{_infodir}/dir

%check
make check

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%{!?_licensedir:%global license %%doc}
%license COPYING COPYING.LIB
%doc AUTHORS README NEWS ChangeLog
%{_prefix}/*

%changelog
* Sun Nov 12 2017 Local EGA build - Frédéric Haziza <daz@nbis.se> - 1.27
- Building for the ingestion worker docker image
