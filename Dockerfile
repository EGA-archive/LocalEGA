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

ARG BUILD_DATE
ARG SOURCE_COMMIT

LABEL maintainer "NeIC System Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.vcs-url="https://github.com/neicnordic/LocalEGA"
LABEL org.label-schema.vcs-ref=$SOURCE_COMMIT


RUN apk add --no-cache --update libressl postgresql-libs

RUN addgroup -g 1000 lega && \
    adduser -D -u 1000 -G lega lega

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

USER 1000

