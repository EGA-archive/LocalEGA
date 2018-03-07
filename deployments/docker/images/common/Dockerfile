FROM python:3.6-alpine3.4
LABEL maintainer "Frédéric Haziza, NBIS"

RUN apk add --update \
    && apk add --no-cache build-base linux-headers bash git postgresql-dev netcat-openbsd openssl-dev libffi-dev \
    && rm -rf /var/cache/apk/*

ARG DEV_PACKAGES=

ARG checkout=
RUN pip install --upgrade pip && \
    pip install git+https://github.com/NBISweden/LocalEGA.git@${checkout}
