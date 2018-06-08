FROM centos:7.4.1708
LABEL maintainer "NBIS System Developers"

ARG DEV_PACKAGES=
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum -y update && \
    yum -y install git gcc make bzip2 nc curl vim-common \
                   zlib-devel bzip2-devel unzip \
                   openssh-server openssl \
		   pam-devel libcurl-devel jq-devel fuse fuse-libs cronie \
		   python36u python36u-pip ${DEV_PACKAGES} && \
    yum clean all && rm -rf /var/cache/yum

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

ENV GOSU_VERSION 1.10
RUN set -ex; \
	\
	yum -y install epel-release; \
	yum -y install wget dpkg; \
	\
	dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
	wget -O /usr/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"; \
	wget -O /tmp/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"; \
	\
# verify the signature
	export GNUPGHOME="$(mktemp -d)"; \
	gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4; \
	gpg --batch --verify /tmp/gosu.asc /usr/bin/gosu; \
	rm -r "$GNUPGHOME" /tmp/gosu.asc; \
	\
	chmod +x /usr/bin/gosu; \
# verify that the binary works
	gosu nobody true; \
	\
	yum -y remove wget dpkg; \
	yum clean all

RUN groupadd -r lega && useradd -M -r -g lega lega

ARG checkout=
ARG PIP_EGA_PACKAGES=
RUN pip3.6 install --upgrade pip && \
    pip3.6 install PyYaml ${PIP_EGA_PACKAGES} && \
    pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}
