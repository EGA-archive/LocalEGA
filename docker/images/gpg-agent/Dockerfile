FROM centos:latest
MAINTAINER Frédéric Haziza, NBIS

RUN yum -y update && \
    yum -y install gcc git curl wget make gettext texinfo \
    	   	   zlib-devel bzip2 bzip2-devel \
		   readline-devel \
		   openssl openssl-devel openssh-server \
		   nss-tools file

ARG LIBGPG_ERROR_VERSION=1.27
ARG LIBGCRYPT_VERSION=1.7.6
ARG LIBASSUAN_VERSION=2.4.3
ARG LIBKSBA_VERSION=1.3.5
ARG LIBNPTH_VERSION=1.3
ARG NCURSES_VERSION=6.0
ARG PINENTRY_VERSION=1.0.0
ARG GNUPG_VERSION=2.1.20
ARG OPENSSH_VERSION=7.5p1

RUN mkdir -p /var/src/{gnupg,openssh} && \
    mkdir -p /root/.gnupg && \
    chmod 700 /root/.gnupg

##############################################################
WORKDIR /var/src/gnupg

# Setup
RUN gpg --list-keys && \
    gpg --keyserver pgp.mit.edu --recv-keys 0x4F25E3B6 0xE0856959 0x33BD3F06 0x7EFD60D9 0xF7E48EDB

# Install libgpg-error
RUN wget -c ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz && \
    wget -c ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz.sig && \
    gpg --verify libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz.sig && tar -xzf libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz && \
    pushd libgpg-error-${LIBGPG_ERROR_VERSION}/ && ./configure && make && make install && popd

# Install libgcrypt
RUN wget -c ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz && \
    wget -c ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz.sig && \
    gpg --verify libgcrypt-${LIBGCRYPT_VERSION}.tar.gz.sig && tar -xzf libgcrypt-${LIBGCRYPT_VERSION}.tar.gz && \
    pushd libgcrypt-${LIBGCRYPT_VERSION} && ./configure && make && make install && popd

# Install libassuan
RUN wget -c ftp://ftp.gnupg.org/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2 && \
    wget -c ftp://ftp.gnupg.org/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2.sig && \
    gpg --verify libassuan-${LIBASSUAN_VERSION}.tar.bz2.sig && tar -xjf libassuan-${LIBASSUAN_VERSION}.tar.bz2 && \
    pushd libassuan-${LIBASSUAN_VERSION} && ./configure && make && make install && popd

# Install libksba
RUN wget -c  ftp://ftp.gnupg.org/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2 && \
    wget -c ftp://ftp.gnupg.org/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2.sig && \
    gpg --verify libksba-${LIBKSBA_VERSION}.tar.bz2.sig && tar -xjf libksba-${LIBKSBA_VERSION}.tar.bz2 && \
    pushd libksba-${LIBKSBA_VERSION} && ./configure && make && make install && popd

# Install libnpth
RUN wget -c ftp://ftp.gnupg.org/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2 && \
    wget -c ftp://ftp.gnupg.org/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2.sig && \
    gpg --verify npth-${LIBNPTH_VERSION}.tar.bz2.sig && tar -xjf npth-${LIBNPTH_VERSION}.tar.bz2 && \
    pushd npth-${LIBNPTH_VERSION} && ./configure && make && make install && popd

# Install ncurses
RUN wget -c ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz && \
    wget -c ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz.sig && \
    gpg --verify ncurses-${NCURSES_VERSION}.tar.gz.sig && tar -xzf ncurses-${NCURSES_VERSION}.tar.gz && \
    pushd ncurses-${NCURSES_VERSION} && export CPPFLAGS="-P" && ./configure && make && make install && popd

# Install pinentry
RUN wget -c ftp://ftp.gnupg.org/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2 && \
    wget -c ftp://ftp.gnupg.org/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2.sig && \
    gpg --verify pinentry-${PINENTRY_VERSION}.tar.bz2.sig && tar -xjf pinentry-${PINENTRY_VERSION}.tar.bz2 && \
    pushd pinentry-${PINENTRY_VERSION} && ./configure --enable-pinentry-curses --disable-pinentry-qt4 && \
    make && make install && popd

# Install 
RUN wget -c ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2 && \
    wget -c ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2.sig && \
    gpg --verify gnupg-${GNUPG_VERSION}.tar.bz2.sig && tar -xjf gnupg-${GNUPG_VERSION}.tar.bz2 && \
    pushd gnupg-${GNUPG_VERSION} && ./configure && make && make install && popd

RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/gpg2.conf && \
    ldconfig -v

##############################################################
WORKDIR /var/src/openssh

RUN gpg --keyserver pgp.mit.edu --recv-keys 0x6D920D30
# Damien Miller <djm@mindrot.org>

RUN wget -c ftp://ftp.eu.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION}.tar.gz && \
    wget -c ftp://ftp.eu.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION}.tar.gz.asc && \
    gpg --verify openssh-${OPENSSH_VERSION}.tar.gz.asc && tar -xzf openssh-${OPENSSH_VERSION}.tar.gz && \
    pushd openssh-${OPENSSH_VERSION} && ./configure && make && make install && popd

##############################################################

# Regenerate keys (no passphrase)
RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

COPY sshd_config /etc/ssh/sshd_config
EXPOSE 22

# Cleaning the previous gpg keys
RUN rm -rf /root/.gnupg && \
    mkdir -p /root/.gnupg && \
    chmod 700 /root/.gnupg

WORKDIR /root/.gnupg
COPY gpg.conf .
COPY gpg-agent.conf .

##############################################################
# Cleanup
RUN rm -rf /var/src/{gnupg,openssh}
WORKDIR /

