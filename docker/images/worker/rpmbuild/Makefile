.PHONY: libgpg-error


all: prepare libgpg-error libgcrypt libassuan libksba npth ncurses pinentry gnupg2

BUILD_OPTS=--define '%debug_package %{nil}' --define '%_prefix /usr/local' --noclean --nocheck

prepare:
	yum -y install gcc curl bzip2 rpm-build zlib-devel bzip2-devel autoconf automake libtool gettext gettext-devel

RPMS/x86_64/libgpg-error-1.27-1.el7.centos.x86_64.rpm: SPECS/libgpg-error.spec
	@echo "Building ${<:SPECS/%.spec=%}"
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/libgcrypt-1.8.1-1.el7.centos.x86_64.rpm: SPECS/libgcrypt.spec RPMS/x86_64/libgpg-error-1.27-1.el7.centos.x86_64.rpm
	@echo "Building ${<:SPECS/%.spec=%}"
	-rpm -i RPMS/x86_64/libgpg-error-1.27-1.el7.centos.x86_64.rpm
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm: SPECS/libassuan.spec
	@echo "Building ${<:SPECS/%.spec=%}"
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/libksba-1.3.5-1.el7.centos.x86_64.rpm: SPECS/libksba.spec
	@echo "Building ${<:SPECS/%.spec=%}"
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/npth-1.5-1.el7.centos.x86_64.rpm: SPECS/npth.spec
	@echo "Building ${<:SPECS/%.spec=%}"
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm: SPECS/ncurses.spec
	@echo "Building ${<:SPECS/%.spec=%}"
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/pinentry-1.0.0-1.el7.centos.x86_64.rpm: SPECS/pinentry.spec ncurses libassuan
	@echo "Building ${<:SPECS/%.spec=%}"
	-rpm -i RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/gnupg-2.2.2-1.el7.centos.x86_64.rpm: SPECS/gnupg2.spec npth libksba libgcrypt
	@echo "Building ${<:SPECS/%.spec=%}"
	-rpm -i RPMS/x86_64/npth-1.5-1.el7.centos.x86_64.rpm RPMS/x86_64/libksba-1.3.5-1.el7.centos.x86_64.rpm RPMS/x86_64/libgcrypt-1.8.1-1.el7.centos.x86_64.rpm
	rpmbuild $(BUILD_OPTS) -ba $<


libgpg-error: RPMS/x86_64/libgpg-error-1.27-1.el7.centos.x86_64.rpm
libgcrypt: RPMS/x86_64/libgcrypt-1.8.1-1.el7.centos.x86_64.rpm
libassuan: RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm
libksba: RPMS/x86_64/libksba-1.3.5-1.el7.centos.x86_64.rpm
npth: RPMS/x86_64/npth-1.5-1.el7.centos.x86_64.rpm
ncurses: RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm
pinentry: RPMS/x86_64/pinentry-1.0.0-1.el7.centos.x86_64.rpm
gnupg2: RPMS/x86_64/gnupg-2.2.2-1.el7.centos.x86_64.rpm
