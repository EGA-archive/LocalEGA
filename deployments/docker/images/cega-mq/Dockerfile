FROM rabbitmq:management
LABEL maintainer "Frédéric Haziza, NBIS"

RUN apt-get update -y && \
    apt-get install -y python3 python3-pika && \
    rm -rf /var/lib/apt/lists/*

COPY rabbitmq.config /etc/rabbitmq/rabbitmq.config
COPY enabled_plugins /etc/rabbitmq/enabled_plugins
COPY publish.py /usr/local/bin/publish
RUN chmod 755 /usr/local/bin/publish
