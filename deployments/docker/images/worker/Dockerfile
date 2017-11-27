FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y install vim-common zlib-devel bzip2-devel

RUN mkdir -p /var/src/ega

COPY rpmbuild/RPMS/x86_64/*.rpm /var/src/ega/
RUN rpm -i /var/src/ega/*.rpm && \
    rm -rf /var/src/ega && \
    echo "/usr/local/lib64" > /etc/ld.so.conf.d/gpg2.conf && \
    ldconfig -v

VOLUME /ega/inbox
VOLUME /ega/staging

ARG checkout=dev
RUN git clone https://github.com/NBISweden/LocalEGA /root/ega && \
    cd /root/ega && \
    git checkout ${checkout} && \
    pip3.6 install /root/ega
#    cd src && \
#    python3.6 setup.py install

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

ENV KEYSERVER_HOST=
ENV KEYSERVER_PORT=
ENV MQ_INSTANCE=
ENTRYPOINT ["entrypoint.sh"]
