FROM rabbitmq:3.6.14-management
LABEL maintainer "Frédéric Haziza, NBIS"

RUN apt-get update && \
    apt-get install -y curl netcat && \
    rm -rf /var/lib/apt/lists/*

RUN rabbitmq-plugins enable --offline rabbitmq_federation && \
    rabbitmq-plugins enable --offline rabbitmq_federation_management && \
    rabbitmq-plugins enable --offline rabbitmq_shovel && \
    rabbitmq-plugins enable --offline rabbitmq_shovel_management

COPY rabbitmq.config /etc/rabbitmq/rabbitmq.config
COPY defs.json /etc/rabbitmq/defs.json
RUN chown rabbitmq:rabbitmq /etc/rabbitmq/rabbitmq.config && \
    chmod 640 /etc/rabbitmq/rabbitmq.config && \
    chown rabbitmq:rabbitmq /etc/rabbitmq/defs.json && \
    chmod 640 /etc/rabbitmq/defs.json

ENV CEGA_CONNECTION=

# See inside the entrypoint for the reason
COPY entrypoint.sh /usr/bin/ega-entrypoint.sh
RUN chmod +x /usr/bin/ega-entrypoint.sh
ENTRYPOINT ["/usr/bin/ega-entrypoint.sh"]
CMD ["rabbitmq-server"]
