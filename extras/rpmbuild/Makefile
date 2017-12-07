BUILD_OPTS=--define '%debug_package %{nil}' --define '%_prefix /usr/local' --noclean --nocheck

all: prepare libgpg-error libgcrypt libassuan libksba npth ncurses pinentry gnupg2

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

RPMS/x86_64/pinentry-1.0.0-1.el7.centos.x86_64.rpm: SPECS/pinentry.spec RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm
	@echo "Building ${<:SPECS/%.spec=%}"
	-rpm -i RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm
	-rpm -i RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm
	rpmbuild $(BUILD_OPTS) -ba $<

RPMS/x86_64/gnupg-2.2.2-1.el7.centos.x86_64.rpm: SPECS/gnupg2.spec SOURCES/gnupg2-socketdir.patch RPMS/x86_64/libgpg-error-1.27-1.el7.centos.x86_64.rpm RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm RPMS/x86_64/npth-1.5-1.el7.centos.x86_64.rpm RPMS/x86_64/libksba-1.3.5-1.el7.centos.x86_64.rpm RPMS/x86_64/libgcrypt-1.8.1-1.el7.centos.x86_64.rpm
	@echo "Building ${<:SPECS/%.spec=%}"
	-rpm -i RPMS/x86_64/libgpg-error-1.27-1.el7.centos.x86_64.rpm
	-rpm -i RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm
	-rpm -i RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm
	-rpm -i RPMS/x86_64/npth-1.5-1.el7.centos.x86_64.rpm 
	-rpm -i RPMS/x86_64/libksba-1.3.5-1.el7.centos.x86_64.rpm
	-rpm -i RPMS/x86_64/libgcrypt-1.8.1-1.el7.centos.x86_64.rpm
	rpmbuild $(BUILD_OPTS) -ba $<

# Create a diff patch. If $? is 0 or >1, then error.
SOURCES/gnupg2-socketdir.patch: SOURCES/gnupg-2.2.2.org/common/homedir.c SOURCES/gnupg-2.2.2/common/homedir.c
	diff -urN --text SOURCES/gnupg-2.2.2.org/common/homedir.c SOURCES/gnupg-2.2.2/common/homedir.c > $@; [ $$? -eq 1 ]

libgpg-error: RPMS/x86_64/libgpg-error-1.27-1.el7.centos.x86_64.rpm
libgcrypt: RPMS/x86_64/libgcrypt-1.8.1-1.el7.centos.x86_64.rpm
libassuan: RPMS/x86_64/libassuan-2.4.3-1.el7.centos.x86_64.rpm
libksba: RPMS/x86_64/libksba-1.3.5-1.el7.centos.x86_64.rpm
npth: RPMS/x86_64/npth-1.5-1.el7.centos.x86_64.rpm
ncurses: RPMS/x86_64/ncurses-6.0-1.el7.centos.x86_64.rpm
pinentry: RPMS/x86_64/pinentry-1.0.0-1.el7.centos.x86_64.rpm
gnupg2: RPMS/x86_64/gnupg-2.2.2-1.el7.centos.x86_64.rpm
diff: SOURCES/gnupg2-socketdir.patch

up:
	docker run -d -it --rm --name rpmbuild -v ${PWD}:/root/rpmbuild centos sleep 1000000000

exec:
	docker exec -it rpmbuild bash

kill:
	docker kill rpmbuild
