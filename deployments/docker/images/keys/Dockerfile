FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN apk add --update \
    && apk add --no-cache openssl-dev libffi-dev \
    && rm -rf /var/cache/apk/*

ARG PIP_EGA_PACKAGES=
RUN pip install PyYaml ${PIP_EGA_PACKAGES}

ENTRYPOINT ["ega-keyserver","--keys","/etc/ega/keys.ini"]
