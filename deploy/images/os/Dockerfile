FROM centos:7.5.1804
LABEL maintainer "NBIS System Developers"

#################################################
##
## Upgrade CentOS 7, and install Python 3.6
##
#################################################

ARG DEV_PACKAGES=
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum -y install epel-release && \
    yum -y update && \
    yum -y install git gcc make bzip2 curl ${DEV_PACKAGES} \
                   zlib-devel bzip2-devel unzip \
		               wget dpkg openssl \
		               python36u python36u-pip

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

#################################################
##
## Install GOSU
##
#################################################

ENV GOSU_VERSION 1.10
ENV GPG_KEYS B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN set -ex && \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" && \
    wget -O /usr/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}" && \
    wget -O /tmp/gosu.asc "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}.asc"

# verify the signature
RUN export GNUPGHOME="$(mktemp -d)" && \
    (gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEYS" \
    || gpg --keyserver pgp.mit.edu --recv-keys "$GPG_KEYS" \
    || gpg --keyserver keyserver.pgp.com --recv-keys "$GPG_KEYS") && \
    gpg --keyserver hkps://hkps.pool.sks-keyservers.net --recv-keys  && \
    gpg --batch --verify /tmp/gosu.asc /usr/bin/gosu && \
    rm -r "$GNUPGHOME" /tmp/gosu.asc && \
    chmod +x /usr/bin/gosu

# verify that the binary works
RUN gosu nobody true && \
    yum -y remove dpkg

#################################################
# Clean up
#################################################

RUN yum clean all && rm -rf /var/cache/yum

#################################################
##
## Install LocalEGA user
##
#################################################

RUN groupadd -r lega && \
    useradd -M -r -g lega lega
