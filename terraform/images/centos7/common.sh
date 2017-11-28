#!/usr/bin/env bash

set -e # stop on errors
set -x # show me the commands

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

# ========================

yum -y install https://centos7.iuscommunity.org/ius-release.rpm
yum -y update
yum -y install gcc git curl make bzip2 unzip patch \
               openssl openssh-server \
	       nss-tools nc nmap tcpdump lsof strace \
	       bash-completion bash-completion-extras \
	       python36u python36u-pip

LIBGPG_ERROR_VERSION=1.27
LIBGCRYPT_VERSION=1.8.1
LIBASSUAN_VERSION=2.4.4
LIBKSBA_VERSION=1.3.5
LIBNPTH_VERSION=1.5
NCURSES_VERSION=6.0
PINENTRY_VERSION=1.0.0
GNUPG_VERSION=2.2.3

mkdir -p /var/src/gnupg && \
mkdir -p /root/{.gnupg,.ssh} && \
chmod 700 /root/{.gnupg,.ssh}

cd /var/src/gnupg

curl -O https://raw.githubusercontent.com/NBISweden/LocalEGA/feature/patch/docker/images/worker/rpmbuild/SOURCES/gnupg2-socketdir.patch

echo "/usr/local/lib" > /etc/ld.so.conf.d/gpg2.conf && \
    ldconfig -v

export PATH=/usr/local/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Setup
gpg --list-keys && \
gpg --keyserver pgp.mit.edu --recv-keys 0x4F25E3B6 0xE0856959 0x33BD3F06 0x7EFD60D9 0xF7E48EDB

# Downloads
#SERVER=ftp://ftp.gnupg.org
SERVER=ftp://mirrors.dotsrc.org
curl -O ${SERVER}/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz
curl -O ${SERVER}/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz.sig
curl -O ${SERVER}/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz
curl -O ${SERVER}/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz.sig
curl -O ${SERVER}/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2
curl -O ${SERVER}/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2.sig
curl -O ${SERVER}/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2
curl -O ${SERVER}/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2.sig
curl -O ${SERVER}/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2
curl -O ${SERVER}/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2.sig
curl -O ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz
curl -O ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz.sig
curl -O ${SERVER}/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2
curl -O ${SERVER}/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2.sig
curl -O ${SERVER}/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2
curl -O ${SERVER}/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2.sig


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
(
    cd libgpg-error-${LIBGPG_ERROR_VERSION}
    ./configure
    make
    make install
)

# Install libgcrypt
(
    cd libgcrypt-${LIBGCRYPT_VERSION}
    ./configure
    make 
    make install
)

# Install libassuan
(
    cd libassuan-${LIBASSUAN_VERSION}
    ./configure
    make 
    make install
)

# Install libksba
(
    cd libksba-${LIBKSBA_VERSION}
    ./configure
    make
    make install
)

# Install libnpth
(
    cd npth-${LIBNPTH_VERSION}
    ./configure 
    make
    make install
)

# Install ncurses
(
    cd ncurses-${NCURSES_VERSION}
    export CPPFLAGS="-P"
    ./configure
    make
    make install
)

# Install pinentry
(
    cd pinentry-${PINENTRY_VERSION}
    ./configure --enable-pinentry-curses --disable-pinentry-qt5 --enable-pinentry-tty
    make
    make install
)

# Install
(
    cd gnupg-${GNUPG_VERSION}
    patch -p1 < /var/src/gnupg/gnupg2-socketdir.patch
    ./configure
    make
    make install
)

##############################################################
# Cleaning the previous gpg keys
cd
rm -rf /root/.gnupg /var/src/gnupg

#################################
# Python 3
#################################

[[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so
[[ -e /usr/local/bin/python3 ]]  || ln -s /bin/python3.6 /usr/local/bin/python3

# Installing required packages
pip3.6 install PyYaml Markdown pika aiohttp pycryptodomex aiopg colorama aiohttp-jinja2

##############################################################
# Create ega user (with default settings)
useradd -m ega

# Update cloud-init
sed -i -e "s/name:\scentos/name: ega/" /etc/cloud/cloud.cfg
sed -i -e "s/gecos:.*/gecos: EGA User/" /etc/cloud/cloud.cfg

# Note: Update the sudo rights?

# Turning it off
poweroff
