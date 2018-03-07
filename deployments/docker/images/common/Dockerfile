FROM python:3.6-alpine3.4
LABEL maintainer "NBIS SysDevs"

RUN apk add --update \
    && apk add --no-cache build-base bash git postgresql-dev netcat-openbsd openssl libffi-dev \
    && rm -rf /var/cache/apk/*

ARG checkout=
ARG PIP_EGA_PACKAGES=
RUN pip install --upgrade pip && \
    pip install PyYaml ${PIP_EGA_PACKAGES} && \
    pip install git+https://github.com/NBISweden/LocalEGA.git@${checkout}


