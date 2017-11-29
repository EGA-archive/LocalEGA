Summary: Ncurses support utilities
Name:    ncurses
Version: 6.0
Release: 1%{?dist}
License: MIT
Group:   System Environment/Base
URL:     http://invisible-island.net/ncurses/ncurses.html

Source0: ftp://ftp.gnu.org/gnu/ncurses/ncurses-%{version}.tar.gz
Source1: ftp://ftp.gnu.org/gnu/ncurses/ncurses-%{version}.tar.gz.sig

%description
The curses library routines are a terminal-independent method of
updating character screens with reasonable optimization.  The ncurses
(new curses) library is a freely distributable replacement for the
discontinued 4.4 BSD classic curses library.

This package contains support utilities, including a terminfo compiler
tic, a decompiler infocmp, clear, tput, tset, and a termcap conversion
tool captoinfo.

%prep
%setup -q

%build
export CPPFLAGS="-P"
%configure --enable-colorfgbg \
	   --enable-hard-tabs \
	   --enable-overwrite \
	   --enable-pc-files \
	   --enable-xmc-glitch \
	   --disable-wattr-macros \
	   --with-cxx-shared \
	   --with-ospeed=unsigned \
	   --with-pkg-config-libdir=%{_libdir}/pkgconfig \
	   --with-shared \
	   --with-terminfo-dirs=%{_sysconfdir}/terminfo:%{_datadir}/terminfo \
	   --with-termlib=tinfo \
	   --with-ticlib=tic \
	   --with-xterm-kbs=DEL \
	   --without-ada
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
#%license COPYING 
#%doc ANNOUNCE AUTHORS NEWS.bz2 README TO-DO
%{_prefix}/*

%changelog
* Sun Nov 12 2017 Local EGA build - Frédéric Haziza <daz@nbis.se> - 1.27
- Building for the ingestion worker docker image

