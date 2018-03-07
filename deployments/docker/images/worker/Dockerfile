FROM nbisweden/ega-common:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN apk add --update \
    && apk add --no-cache postgresql-dev libffi-dev netcat-openbsd

VOLUME /ega/inbox
VOLUME /ega/staging

ARG PIP_EGA_PACKAGES=

RUN pip install PyYaml ${PIP_EGA_PACKAGES}

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

ENV KEYSERVER_INSTANCE=
ENV MQ_INSTANCE=
ENTRYPOINT ["entrypoint.sh"]
