##########################
## Build env
##########################
FROM python:3.6-alpine3.10 as BUILD

RUN apk add git postgresql-dev gcc musl-dev libffi-dev make gnupg

COPY requirements.txt /root/LocalEGA/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /root/LocalEGA/requirements.txt

COPY setup.py /root/LocalEGA/setup.py
COPY lega /root/LocalEGA/lega
RUN pip install /root/LocalEGA


##########################
## Final image
##########################
FROM python:3.6-alpine3.10

LABEL maintainer "EGA System Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"


RUN apk add --no-cache --update libressl postgresql-libs

ARG LEGA_UID=1000
ARG LEGA_GID=1000

RUN addgroup -g ${LEGA_GID} lega && \
    adduser -D -G lega -u ${LEGA_UID} lega

COPY --from=BUILD usr/local/lib/python3.6/ usr/local/lib/python3.6/

COPY --from=BUILD /usr/local/bin/ega-* /usr/local/bin/

RUN mkdir -p /ega/archive && \
    chgrp lega /ega/archive && \
    chmod 2770 /ega/archive
VOLUME /ega/archive

RUN mkdir -p /etc/ega && \
    chgrp lega /etc/ega && \
    chmod 2770 /etc/ega
VOLUME /etc/ega

USER lega

