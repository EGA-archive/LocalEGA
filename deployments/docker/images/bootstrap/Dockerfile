FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum -y install openssl vim-common && \
    yum clean all && rm -rf /var/cache/yum

ARG PIP_EGA_PACKAGES=

RUN pip3.6 install PyYaml ${PIP_EGA_PACKAGES}

VOLUME /ega
ENTRYPOINT ["/ega/bootstrap/boot.sh"]
