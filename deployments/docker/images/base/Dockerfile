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

ARG checkout=
ARG PIP_EGA_PACKAGES=
RUN pip3.6 install --upgrade pip && \
    pip3.6 install PyYaml ${PIP_EGA_PACKAGES} && \
    pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}


