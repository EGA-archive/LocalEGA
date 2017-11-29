Summary: Utility for secure communication and data storage
Name:    gnupg
Version: 2.2.2
Release: 1%{?dist}
License: GPLv3+
Group:   Applications/System
URL:     http://www.gnupg.org/
Source0: ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-%{version}.tar.bz2
Source1: ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-%{version}.tar.bz2.sig
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Patch0:  gnupg2-socketdir.patch

# BuildRequires: bzip2-devel
# BuildRequires: openldap-devel
# BuildRequires: libusb-devel
# BuildRequires: pcsc-lite-libs
# BuildRequires: readline-devel
# BuildRequires: zlib-devel
# BuildRequires: gnutls-devel
# BuildRequires: sqlite-devel
# BuildRequires: fuse

Requires: libgcrypt >= 1.7.0

# Recommends: pinentry
# Recommends: gnupg2-smime

Provides: gpg = %{version}-%{release}
# Obsolete GnuPG-1 package
Provides: gnupg = %{version}-%{release}
Obsoletes: gnupg <= 1.4.10

Provides: dirmngr = %{version}-%{release}
Obsoletes: dirmngr < 1.2.0-1

%description
GnuPG is GNU\'s tool for secure communication and data storage.  It can
be used to encrypt data and to create digital signatures.  It includes
an advanced key management facility and is compliant with the proposed
OpenPGP Internet standard as described in RFC2440 and the S/MIME
standard as described by several RFCs.

GnuPG 2.0 is a newer version of GnuPG with additional support for
S/MIME.  It has a different design philosophy that splits
functionality up into several modules. The S/MIME and smartcard functionality
is provided by the gnupg2-smime package.

%prep
%setup -q
%patch0 -p1

%build
%configure --enable-gpg-is-gpg2 \
  --disable-gpgtar \
  --disable-rpath \
  --disable-doc

make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
rm -f %{buildroot}/%{_infodir}/dir

%check
# need scratch gpg database for tests
mkdir -p %{buildroot}/gnupg_home
export GNUPGHOME=%{buildroot}/gnupg_home
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib64
make -k check

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%{!?_licensedir:%global license %%doc}
#%license COPYING 
#doc AUTHORS NEWS README THANKS TODO
%{_prefix}/*

%changelog
* Sun Nov 12 2017 Local EGA build - Frédéric Haziza <daz@nbis.se> - 1.27
- Building for the ingestion worker docker image

