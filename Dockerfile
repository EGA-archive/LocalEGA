FROM python:3.6-alpine3.8 as BUILD

RUN apk add git postgresql-dev gcc musl-dev libffi-dev make gnupg

COPY setup.py /root/LocalEGA/setup.py
COPY lega /root/LocalEGA/lega
COPY requirements.txt /root/LocalEGA/requirements.txt

RUN pip install -r /root/LocalEGA/requirements.txt && \
    pip install /root/LocalEGA

FROM python:3.6-alpine3.8

ARG BUILD_DATE
ARG SOURCE_COMMIT

LABEL maintainer "EGA System Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"
LABEL org.label-schema.vcs-ref=$SOURCE_COMMIT


RUN apk add --no-cache --update libressl postgresql-libs

ARG LEGA_GID=1000

RUN addgroup -g ${LEGA_GID} lega && \
    adduser -D -G lega lega

COPY --from=BUILD usr/local/lib/python3.6/ usr/local/lib/python3.6/

COPY --from=BUILD /usr/local/bin/lega-cryptor /usr/local/bin/

COPY --from=BUILD /usr/local/bin/ega-* /usr/local/bin/

VOLUME /etc/ega

USER lega
