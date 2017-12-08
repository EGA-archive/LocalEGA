Name:    libassuan
Summary: GnuPG IPC library
Version: 2.4.3
Release: 1%{?dist}
License: LGPLv2+ and GPLv3+
Source0: https://gnupg.org/ftp/gcrypt/libassuan/libassuan-%{version}.tar.bz2
Source1: https://gnupg.org/ftp/gcrypt/libassuan/libassuan-%{version}.tar.bz2.sig

BuildRequires: gawk
#BuildRequires: libgpg-error-devel >= 1.8

%description
This is the IPC library used by GnuPG 2, GPGME and a few other packages.

%prep
%setup -q

%build
%configure --disable-static --disable-doc
make %{?_smp_mflags}

%check
make check

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
rm -f %{buildroot}/%{_libdir}/*.la %{buildroot}/%{_infodir}/dir

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%{!?_licensedir:%global license %%doc}
%license COPYING COPYING.LIB
%doc AUTHORS NEWS THANKS
%{_prefix}/*

%changelog
* Sun Nov 12 2017 Local EGA build - Frédéric Haziza <daz@nbis.se> - 1.27
- Building for the ingestion worker docker image
