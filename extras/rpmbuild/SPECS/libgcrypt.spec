Name: libgcrypt
Version: 1.8.1
Release: 1%{?dist}
Source0: libgcrypt-%{version}.tar.bz2
License: LGPLv2+
Summary: A general-purpose cryptography library
Group: System Environment/Libraries

%description
Libgcrypt is a general purpose crypto library based on the code used
in GNU Privacy Guard.  This is a development version.

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
