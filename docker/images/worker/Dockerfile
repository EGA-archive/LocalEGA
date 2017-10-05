FROM nbis/ega:common
LABEL maintainer "Frédéric Haziza, NBIS"

# Setup
RUN gpg --list-keys && \
    gpg --keyserver pgp.mit.edu --recv-keys 0x4F25E3B6 0xE0856959 0x33BD3F06 0x7EFD60D9 0xF7E48EDB

##############################################################

ARG LIBGPG_ERROR_VERSION=1.27
ARG LIBGCRYPT_VERSION=1.8.1
ARG LIBASSUAN_VERSION=2.4.3
ARG LIBKSBA_VERSION=1.3.5
ARG LIBNPTH_VERSION=1.5
ARG NCURSES_VERSION=6.0
ARG PINENTRY_VERSION=1.0.0
ARG GNUPG_VERSION=2.2.1

##############################################################
RUN mkdir -p /var/src/gnupg
WORKDIR /var/src/gnupg

# To get compression capabilities inside GnuPG
RUN yum -y install zlib-devel bzip2-devel

# Install libgpg-error
RUN curl -O ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz && \
    curl -O ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz.sig && \
    gpg --verify libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz.sig && tar -xzf libgpg-error-${LIBGPG_ERROR_VERSION}.tar.gz && \
    pushd libgpg-error-${LIBGPG_ERROR_VERSION}/ && ./configure && make && make install && popd

# Install libgcrypt
RUN curl -O ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz && \
    curl -O ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-${LIBGCRYPT_VERSION}.tar.gz.sig && \
    gpg --verify libgcrypt-${LIBGCRYPT_VERSION}.tar.gz.sig && tar -xzf libgcrypt-${LIBGCRYPT_VERSION}.tar.gz && \
    pushd libgcrypt-${LIBGCRYPT_VERSION} && ./configure && make && make install && popd

# Install libassuan
RUN curl -O ftp://ftp.gnupg.org/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2 && \
    curl -O ftp://ftp.gnupg.org/gcrypt/libassuan/libassuan-${LIBASSUAN_VERSION}.tar.bz2.sig && \
    gpg --verify libassuan-${LIBASSUAN_VERSION}.tar.bz2.sig && tar -xjf libassuan-${LIBASSUAN_VERSION}.tar.bz2 && \
    pushd libassuan-${LIBASSUAN_VERSION} && ./configure && make && make install && popd

# Install libksba
RUN curl -O  ftp://ftp.gnupg.org/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2 && \
    curl -O ftp://ftp.gnupg.org/gcrypt/libksba/libksba-${LIBKSBA_VERSION}.tar.bz2.sig && \
    gpg --verify libksba-${LIBKSBA_VERSION}.tar.bz2.sig && tar -xjf libksba-${LIBKSBA_VERSION}.tar.bz2 && \
    pushd libksba-${LIBKSBA_VERSION} && ./configure && make && make install && popd

# Install libnpth
RUN curl -O ftp://ftp.gnupg.org/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2 && \
    curl -O ftp://ftp.gnupg.org/gcrypt/npth/npth-${LIBNPTH_VERSION}.tar.bz2.sig && \
    gpg --verify npth-${LIBNPTH_VERSION}.tar.bz2.sig && tar -xjf npth-${LIBNPTH_VERSION}.tar.bz2 && \
    pushd npth-${LIBNPTH_VERSION} && ./configure && make && make install && popd

# Install ncurses
RUN curl -O ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz && \
    curl -O ftp://ftp.gnu.org/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz.sig && \
    gpg --verify ncurses-${NCURSES_VERSION}.tar.gz.sig && tar -xzf ncurses-${NCURSES_VERSION}.tar.gz && \
    pushd ncurses-${NCURSES_VERSION} && export CPPFLAGS="-P" && ./configure && make && make install && popd

# Install pinentry
RUN curl -O ftp://ftp.gnupg.org/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2 && \
    curl -O ftp://ftp.gnupg.org/gcrypt/pinentry/pinentry-${PINENTRY_VERSION}.tar.bz2.sig && \
    gpg --verify pinentry-${PINENTRY_VERSION}.tar.bz2.sig && tar -xjf pinentry-${PINENTRY_VERSION}.tar.bz2 && \
    pushd pinentry-${PINENTRY_VERSION} && ./configure --enable-pinentry-curses --disable-pinentry-qt5 --enable-pinentry-tty && \
    make && make install && popd

# Install 
RUN curl -O ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2 && \
    curl -O ftp://ftp.gnupg.org/gcrypt/gnupg/gnupg-${GNUPG_VERSION}.tar.bz2.sig && \
    gpg --verify gnupg-${GNUPG_VERSION}.tar.bz2.sig && tar -xjf gnupg-${GNUPG_VERSION}.tar.bz2 && \
    pushd gnupg-${GNUPG_VERSION} && ./configure && make && make install && popd

RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/gpg2.conf && \
    ldconfig -v

##############################################################
# Cleaning up
RUN rm -rf /var/src/gnupg && \
    rm -rf /root/.gnupg && \
    mkdir -p /root/.gnupg && \
    chmod 700 /root/.gnupg && \
    mkdir -p /var/run/ega

WORKDIR /

# For the xxd utility
RUN yum -y install vim-common
