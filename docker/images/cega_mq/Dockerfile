FROM rabbitmq:management
LABEL maintainer "Frédéric Haziza, NBIS"

COPY rabbitmq.config /etc/rabbitmq/rabbitmq.config

# Add your defs.json from the template file
COPY rabbitmq.conf.tpl /etc/rabbitmq/defs.json
