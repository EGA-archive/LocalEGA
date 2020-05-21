FROM postgres:12.1-alpine

LABEL maintainer "EGA System Developers"
LABEL org.label-schema.schema-version="2.1"
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"

ENV SSL_SUBJ             /C=ES/ST=Spain/L=Barcelona/O=CRG/OU=SysDevs/CN=LocalEGA/emailAddress=dev.ega@crg.eu
ENV TZ                   Europe/Madrid
ENV PGDATA               /ega/data

EXPOSE 5432
VOLUME /ega/data

RUN apk add --no-cache openssl


RUN mkdir -p /etc/ega/initdb.d            && \
    mkdir -p /var/run/postgresql          && \
    chmod 2775 /var/run/postgresql

COPY pg.conf       /etc/ega/pg.conf.default
COPY initdb.d      /etc/ega/initdb.d

RUN chown -R postgres /etc/ega            && \
    chown -R postgres /var/run/postgresql

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
