# FROM python:3.6-alpine3.7
#
# RUN apk add --update && \
#     apk add --no-cache build-base libffi-dev openssl-dev linux-headers bash git && \
#     rm -rf /var/cache/apk/*
#
# ENV KEYSERVER_PORT=
# ARG PIP_EGA_PACKAGES=
#
# RUN pip install PyYaml ${PIP_EGA_PACKAGES}
#
# ARG checkout=
# #RUN pip install --upgrade git+https://github.com/NBISweden/LocalEGA.git@${checkout}
# RUN git clone https://github.com/NBISweden/LocalEGA.git /tmp/LocalEGA && \
#     cd /tmp/LocalEGA && \
#     git checkout ${checkout} && \
#     cd / && \
#     pip install /tmp/LocalEGA
#
# ENTRYPOINT ["/usr/local/bin/ega-keyserver","--keys","/etc/ega/keys.ini"]


FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

ARG PIP_EGA_PACKAGES=

RUN pip3.6 install PyYaml ${PIP_EGA_PACKAGES}

ENV KEYSERVER_PORT=
ENTRYPOINT ["/bin/ega-keyserver","--keys","/etc/ega/keys.ini"]
