FROM rabbitmq:3.9.11-management-alpine

LABEL maintainer="EGA System Developers"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.vcs-url="https://github.com/EGA-archive/LocalEGA"

VOLUME /var/lib/rabbitmq

RUN apk add --no-cache ca-certificates

RUN rabbitmq-plugins enable --offline rabbitmq_federation rabbitmq_federation_management rabbitmq_shovel rabbitmq_shovel_management

COPY entrypoint.sh /usr/local/bin/ega-entrypoint.sh

RUN chmod +x /usr/local/bin/ega-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/ega-entrypoint.sh"]

CMD ["rabbitmq-server"]
