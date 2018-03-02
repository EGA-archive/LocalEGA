FROM python:3.6-alpine3.7

RUN apk add --update \
    && apk add --no-cache build-base libffi-dev openssl-dev linux-headers bash git \
    && rm -rf /var/cache/apk/*

ENV KEYSERVER_PORT=
ARG PIP_EGA_PACKAGES=

RUN pip install PyYaml ${PIP_EGA_PACKAGES}

RUN mkdir -p /keyserver \
    && chmod +x /keyserver

ARG checkout=
RUN pip install git+https://github.com/NBISweden/LocalEGA.git@${checkout}

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
