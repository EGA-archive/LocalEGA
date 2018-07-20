FROM centos:7.4.1708
LABEL maintainer "NBIS System Developers"

ARG DEV_PACKAGES=
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum -y install epel-release && \
    yum -y update && \
    yum -y install git gcc make bzip2 curl \
                   zlib-devel bzip2-devel unzip \
                   openssh-server openssl \
		   wget dpkg \
		   pam-devel libcurl-devel jq-devel fuse fuse-libs cronie \
		   python36u python36u-pip ${DEV_PACKAGES}

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

ENV GOSU_VERSION 1.10
ENV GPG_KEYS B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN set -ex && \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" && \
    wget -O /usr/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}" && \
    wget -O /tmp/gosu.asc "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}.asc"

# verify the signature
RUN export GNUPGHOME="$(mktemp -d)" && \
    gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEYS" \
    || gpg --keyserver pgp.mit.edu --recv-keys "$GPG_KEYS" \
    || gpg --keyserver keyserver.pgp.com --recv-keys "$GPG_KEYS" && \
    gpg --keyserver hkps://hkps.pool.sks-keyservers.net --recv-keys  && \
    gpg --batch --verify /tmp/gosu.asc /usr/bin/gosu && \
    rm -r "$GNUPGHOME" /tmp/gosu.asc && \
    chmod +x /usr/bin/gosu

# verify that the binary works
RUN gosu nobody true && \
    yum -y remove dpkg

RUN yum clean all && rm -rf /var/cache/yum

RUN groupadd -r lega && useradd -M -r -g lega lega

ARG checkout=
ARG PIP_EGA_PACKAGES=
RUN pip3.6 install --upgrade pip && \
    pip3.6 install PyYaml ${PIP_EGA_PACKAGES}

RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}

RUN pip3.6 install git+https://github.com/NBISweden/LocalEGA-cryptor.git
