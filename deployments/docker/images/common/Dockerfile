FROM centos:7.4.1708
LABEL maintainer "Frédéric Haziza, NBIS"

ARG DEV_PACKAGES=

RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum -y update && \
    yum -y install git gcc make bzip2 python36u python36u-pip ${DEV_PACKAGES} && \
    yum clean all && rm -rf /var/cache/yum

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

ARG checkout=
RUN pip3.6 install --upgrade pip && \
    pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@${checkout}
