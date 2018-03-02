FROM python:3.6-alpine3.7

RUN apk add --update \
    && apk add --no-cache build-base \
    && apk add --no-cache libffi-dev openssl-dev \
    && apk add --no-cache linux-headers \
    && apk add --no-cache bash \
    && apk add --no-cache git \
&& rm -rf /var/cache/apk/*

ENV KEYSERVER_PORT=
ARG PIP_EGA_PACKAGES=

RUN pip install PyYaml aiohttp cryptography ${PIP_EGA_PACKAGES}

RUN mkdir -p /keyserver \
    && chmod +x /keyserver

RUN cd /keyserver \
    && git clone git://github.com/NBISweden/LocalEGA.git . \
    && git checkout feature/pgp-keyserver \
    && pip install -e ./

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["dumb-init", "--"]
ENTRYPOINT ["/entrypoint.sh"]
