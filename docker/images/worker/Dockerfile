FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y install vim-common zlib-devel bzip2-devel

RUN mkdir -p /var/src/ega

COPY rpmbuild/RPMS/x86_64/*.rpm /var/src/ega/

RUN rpm -i /var/src/ega/*.rpm && \
    rm -rf /var/src/ega && \
    echo "/usr/local/lib64" > /etc/ld.so.conf.d/gpg2.conf && \
    ldconfig -v
