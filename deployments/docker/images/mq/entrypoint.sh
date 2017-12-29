#!/bin/bash

set -e
set -x

[[ -z "${INSTANCE}" ]] && echo 'Environment INSTANCE is empty' 1>&2 && exit 1
[[ -z "${CEGA_MQ_PASSWORD}" ]] && echo 'Environment CEGA_MQ_PASSWORD is empty' 1>&2 && exit 1

# Problem of loading the plugins and definitions out-of-orders.
# Explanation: https://github.com/rabbitmq/rabbitmq-shovel/issues/13
# Therefore: we run the server, with some default confs
# and then we upload the cega-definitions through the HTTP API

# We cannot add those definitions to defs.json (loaded by the
# management plugin. See /etc/rabbitmq/rabbitmq.config)
# So we use curl afterwards, to upload the extras definitions
# See also https://pulse.mozilla.org/api/

# For the moment, still using guest:guest
cat > /etc/rabbitmq/defs-cega.json <<EOF
{"parameters":[{"value":{"src-uri":"amqp://",
			 "src-exchange":"lega",
			 "src-exchange-key":"lega.error.user",
			 "dest-uri":"amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega_mq:5672/${INSTANCE}",
			 "dest-exchange":"localega.v1",
			 "dest-exchange-key":"errors",
			 "add-forward-headers":false,
			 "ack-mode":"on-confirm",
			 "delete-after":"never"},
		"vhost":"/",
		"component":"shovel",
		"name":"CEGA-errors"},
	       {"value":{"src-uri":"amqp://",
			 "src-exchange":"lega",
			 "src-exchange-key":"lega.completed",
			 "dest-uri":"amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega_mq:5672/${INSTANCE}",
			 "dest-exchange":"localega.v1",
			 "dest-exchange-key":"completed",
			 "add-forward-headers":false,
			 "ack-mode":"on-confirm",
			 "delete-after":"never"},
		"vhost":"/",
		"component":"shovel",
		"name":"CEGA-completion"},
	       {"value":{"src-uri":"amqp://",
			 "src-exchange":"lega",
			 "src-exchange-key":"lega.inbox",
			 "dest-uri":"amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega_mq:5672/${INSTANCE}",
			 "dest-exchange":"localega.v1",
			 "dest-exchange-key":"inbox",
			 "add-forward-headers":false,
			 "ack-mode":"on-confirm",
			 "delete-after":"never"},
		"vhost":"/",
		"component":"shovel",
		"name":"CEGA-inbox"},
	       {"value":{"uri":"amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega_mq:5672/${INSTANCE}",
			 "ack-mode":"on-confirm",
			 "trust-user-id":false,
			 "queue":"file"},
		"vhost":"/",
		"component":"federation-upstream",
		"name":"CEGA"}],
 "policies":[{"vhost":"/","name":"CEGA","pattern":"files","apply-to":"queues","definition":{"federation-upstream":"CEGA"},"priority":0}]
}
EOF
chown rabbitmq:rabbitmq /etc/rabbitmq/defs-cega.json
chmod 640 /etc/rabbitmq/defs-cega.json

# And...cue music
chown -R rabbitmq /var/lib/rabbitmq

{ # Spawn off
    sleep 5 # Small delay first
    
    # Wait until the server is ready (on the management port)
    until nc -z 127.0.0.1 15672; do sleep 1; done
    ROUND=30
    until curl -X POST -u guest:guest -H "Content-Type: application/json" --data @/etc/rabbitmq/defs-cega.json http://127.0.0.1:15672/api/definitions || ((ROUND<0))
    do
	sleep 1
	$((ROUND--))
    done
    ((ROUND<0)) && echo "Central EGA connections *_not_* loaded" 2>&1 && exit 1
    echo "Central EGA connections loaded"
} &

exec "$@" # ie CMD rabbitmq-server
