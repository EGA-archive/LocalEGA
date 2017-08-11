#!/usr/bin/env bash

set -e # stop on errors
set -x # show me the commands


yum -y update && \
yum -y install gcc git curl wget make gettext texinfo \
               zlib-devel bzip2 bzip2-devel \
	       file readline-devel \
	       sqlite sqlite-devel \
	       openssl openssl-devel openssh-server \
	       nss-tools nc nmap tcpdump lsof

LIBGPG_ERROR_VERSION=1.27
LIBGCRYPT_VERSION=1.7.6
LIBASSUAN_VERSION=2.4.3
LIBKSBA_VERSION=1.3.5
LIBNPTH_VERSION=1.3
NCURSES_VERSION=6.0
PINENTRY_VERSION=1.0.0
GNUPG_VERSION=2.1.20
OPENSSH_VERSION=7.5p1

mkdir -p /var/src/{gnupg,openssh} && \
mkdir -p /root/{.gnupg,.ssh} && \
chmod 700 /root/{.gnupg,.ssh}

cd /var/src/gnupg

echo "/usr/local/lib" > /etc/ld.so.conf.d/gpg2.conf && \
    ldconfig -v

export PATH=/usr/local/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Setup
gpg --list-keys && \
gpg --keyserver pgp.mit.edu --recv-keys 0x4F25E3B6 0xE0856959 0x33BD3F06 0x7EFD60D9 0xF7E48EDB

# Downloads
wget -c ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz
wget -c ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz.sig
wget -c ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz
wget -c ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz.sig
wget -c ftp://ftp.gnupg.org/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2
wget -c ftp://ftp.gnupg.org/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2.sig
wget -c ftp://ftp.gnupg.org/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2
wget -c ftp://ftp.gnupg.org/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2.sig
wget -c ftp://ftp.gnupg.org/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2
wget -c ftp://ftp.gnupg.org/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2.sig
wget -c ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz
wget -c ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz.sig
wget -c ftp://ftp.gnupg.org/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2
wget -c ftp://ftp.gnupg.org/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2.sig
wget -c ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2
wget -c ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2.sig


# Verify and uncompress
gpg --verify libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz.sig && tar -xzf libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz
gpg --verify libgcrypt-${LIBGCRYPT_VERSION}.tar.gz.sig && tar -xzf libgcrypt-${LIBGCRYPT_VERSION}.tar.gz
gpg --verify libassuan-${LIBASSUAN_VERSION}.tar.bz2.sig && tar -xjf libassuan-${LIBASSUAN_VERSION}.tar.bz2
gpg --verify libksba-${LIBKSBA_VERSION}.tar.bz2.sig && tar -xjf libksba-${LIBKSBA_VERSION}.tar.bz2
gpg --verify npth-${LIBNPTH_VERSION}.tar.bz2.sig && tar -xjf npth-${LIBNPTH_VERSION}.tar.bz2
gpg --verify ncurses-${NCURSES_VERSION}.tar.gz.sig && tar -xzf ncurses-${NCURSES_VERSION}.tar.gz
gpg --verify pinentry-${PINENTRY_VERSION}.tar.bz2.sig && tar -xjf pinentry-${PINENTRY_VERSION}.tar.bz2
gpg --verify gnupg-${GNUPG_VERSION}.tar.bz2.sig && tar -xjf gnupg-${GNUPG_VERSION}.tar.bz2


# Install libgpg-error
pushd libgpg-error-${LIBGPG_ERROR_VERSION}/ && ./configure && make && make install && popd

# Install libgcrypt
pushd libgcrypt-${LIBGCRYPT_VERSION} && ./configure && make && make install && popd

# Install libassuan
pushd libassuan-${LIBASSUAN_VERSION} && ./configure && make && make install && popd

# Install libksba
pushd libksba-${LIBKSBA_VERSION} && ./configure && make && make install && popd

# Install libnpth
pushd npth-${LIBNPTH_VERSION} && ./configure && make && make install && popd

# Install ncurses
pushd ncurses-${NCURSES_VERSION} && export CPPFLAGS="-P" && ./configure && make && make install && popd

# Install pinentry
pushd pinentry-${PINENTRY_VERSION} && ./configure --enable-pinentry-curses --disable-pinentry-qt5 --enable-pinentry-tty && \
make && make install && popd

# Install 
pushd gnupg-${GNUPG_VERSION} && ./configure && make && make install && popd


##############################################################
cd /var/src/openssh

gpg --keyserver pgp.mit.edu --recv-keys 0x6D920D30
# Damien Miller <djm@mindrot.org>

wget -c ftp://ftp.eu.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION}.tar.gz
wget -c ftp://ftp.eu.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION}.tar.gz.asc
gpg --verify openssh-${OPENSSH_VERSION}.tar.gz.asc && tar -xzf openssh-${OPENSSH_VERSION}.tar.gz
pushd openssh-${OPENSSH_VERSION} && ./configure && make && make install && popd

##############################################################
# Cleaning the previous gpg keys
rm -rf /root/.gnupg && \
mkdir -p /root/.gnupg && \
chmod 700 /root/.gnupg

##############################################################
# Cleanup
cd /
rm -rf /var/src/{gnupg,openssh}


#################################
# Python 3
#################################

yum -y install https://centos7.iuscommunity.org/ius-release.rpm
yum -y install python36u
yum -y install python36u-pip

ln -s /bin/python3.6 /usr/local/bin/python3
