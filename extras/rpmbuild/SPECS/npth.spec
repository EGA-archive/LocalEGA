Summary:   The New GNU Portable Threads library
Name:      npth
Version:   1.5
Release:   1%{?dist}
License:   LGPLv2+
URL:       http://git.gnupg.org/cgi-bin/gitweb.cgi?p=npth.git
Group:     System Environment/Libraries
Source0:   ftp://ftp.gnupg.org/gcrypt/%{name}/%{name}-%{version}.tar.bz2
Source1:   ftp://ftp.gnupg.org/gcrypt/%{name}/%{name}-%{version}.tar.bz2.sig
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  make, gcc

%description
nPth is a non-preemptive threads implementation using an API very similar
to the one known from GNU Pth. It has been designed as a replacement of
GNU Pth for non-ancient operating systems. In contrast to GNU Pth is is
based on the system\'s standard threads implementation. Thus nPth allows
the use of libraries which are not compatible to GNU Pth.

%prep
%setup -q

%build
%configure --disable-static --disable-doc
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
#%license COPYING
#%doc AUTHORS README NEWS ChangeLog
%{_prefix}/*

%changelog
* Sun Nov 12 2017 Local EGA build - Frédéric Haziza <daz@nbis.se> - 1.27
- Building for the ingestion worker docker image
