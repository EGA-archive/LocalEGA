FROM centos:latest
MAINTAINER Frédéric Haziza, NBIS

RUN yum -y update && \
    yum -y install gcc git curl wget make gettext texinfo \
    	   	   zlib-devel bzip2 bzip2-devel \
		   readline-devel \
		   openssl openssl-devel openssh-server \
		   nss-tools

ENV LIBGPG_ERROR_VERSION 1.27
ENV LIBGCRYPT_VERSION 1.7.6
ENV LIBASSUAN_VERSION 2.4.3
ENV LIBKSBA_VERSION 1.3.5
ENV LIBNPTH_VERSION 1.3
ENV NCURSES_VERSION 6.0
ENV PINENTRY_VERSION 1.0.0
ENV GNUPG_VERSION 2.1.20

# Setup
RUN mkdir -p /var/src/gnupg21 && \
    gpg --list-keys && \
    gpg --recv-keys 0x4F25E3B6 0xE0856959 0x33BD3F06 0x7EFD60D9 0xF7E48EDB

WORKDIR /var/src/gnupg21

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

RUN mkdir -p /root/.gnupg
WORKDIR /root/.gnupg
# RUN rm -rf /var/src/gnupg21

COPY gpg.conf gpg.conf
COPY gpg-agent.conf gpg-agent.conf

COPY sshd_config /etc/ssh/sshd_config
EXPOSE 22

WORKDIR /
CMD sleep 360000

