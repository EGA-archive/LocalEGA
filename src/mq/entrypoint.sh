#!/usr/bin/env bash

set -eo pipefail

[[ -z "${CEGA_CONNECTION}" ]] && echo 'Environment variable CEGA_CONNECTION is empty' 1>&2 && exit 1
[[ -z "${MQ_USER}" ]] && export MQ_USER='admin'
[[ -z "${MQ_PASSWORD_HASH}" ]] && export MQ_PASSWORD_HASH='IUBfMYLSSPynj8zjLxX3DtEHi0fhcKPhY/Cy7MJhrragBeP8'

cat > /etc/rabbitmq/rabbitmq.conf <<EOF
disk_free_limit.absolute = 1GB
management.listener.port = 15672
management.load_definitions = /etc/rabbitmq/definitions.json
EOF

cat > /etc/rabbitmq/definitions.json <<EOF
{
  "users": [
    {
      "name": "${MQ_USER}", "password_hash": "${MQ_PASSWORD_HASH}",
      "hashing_algorithm": "rabbit_password_hashing_sha256", "tags": "administrator"
    }
  ],
  "vhosts": [
    { "name": "/" }
  ],
  "permissions": [
    { "user": "${MQ_USER}", "vhost": "/", "configure": ".*", "write": ".*", "read": ".*" }
  ],
  "parameters": [
    {
      "name": "from_cega", "vhost": "/", "component": "federation-upstream",
      "value": { "ack-mode": "on-confirm", "queue": "to_${AFFILIATE_NAME:-fega}"",
		 "trust-user-id": false, "uri": "${CEGA_CONNECTION}" }
    }
  ],
  "policies": [
    {
      "vhost": "/", "name": "from_cega", "pattern": "from_cega", "apply-to": "queues", "priority": 0,
      "definition": { "federation-upstream": "from_cega" }
    }
  ],
  "queues": [
    {"name": "from_cega", "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "errors",    "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "system.errors",    "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "to_cega",   "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "lega.all", "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}}
  ],
  "exchanges": [
    {"name":"cega", "vhost":"/", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{}}, 
    {"name":"lega", "vhost":"/", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{}}
  ], 
  "bindings": [
    { "source":"cega", "vhost": "/", "destination":"errors", "destination_type":"queue", "routing_key":"files.error", "arguments":{}},
    { "source":"cega", "vhost": "/", "destination":"to_cega", "destination_type":"queue", "routing_key":"#", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"system.errors", "destination_type":"queue", "routing_key":"system.error", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"lega.all", "destination_type":"queue", "routing_key":"#", "arguments":{}}
  ]
}
EOF

cat > /etc/rabbitmq/advanced.config <<EOF
[
 {rabbitmq_shovel,
  [{shovels, [{to_cega, [{source, [{protocol, amqp091},
				   {uris, ["amqp://"]},
				   {declarations, []},
				   {queue, <<"to_cega">>},
				   {prefetch_count, 1000}]
			 },
			 {destination, [{protocol, amqp091},
					{uris, ["${CEGA_CONNECTION}"]},
					{declarations, []},
					{publish_properties, [{delivery_mode, 2}]},
					{publish_fields, [{exchange, <<"${AFFILIATE_NAME:-localega}">>}]}]
			 },
			 {ack_mode, on_confirm},
			 {reconnect_delay, 5}
			]
	      }]
    }
  ]}
].
EOF

cat > /etc/rabbitmq/enabled_plugins <<EOF
[rabbitmq_federation,rabbitmq_federation_management,rabbitmq_shovel,rabbitmq_shovel_management].
EOF

chown rabbitmq:rabbitmq /etc/rabbitmq/definitions.json
chown rabbitmq:rabbitmq /etc/rabbitmq/enabled_plugins
chown rabbitmq:rabbitmq /etc/rabbitmq/advanced.config
chown rabbitmq:rabbitmq /etc/rabbitmq/rabbitmq.conf

chmod 600 /etc/rabbitmq/definitions.json
chmod 600 /etc/rabbitmq/enabled_plugins
chmod 600 /etc/rabbitmq/advanced.config
chmod 600 /etc/rabbitmq/rabbitmq.conf

# allow the container to be started with `--user`
if [[ "$1" == rabbitmq* ]] && [ "$(id -u)" = '0' ]; then
	if [ "$1" = 'rabbitmq-server' ]; then
		find /var/lib/rabbitmq \! -user rabbitmq -exec chown rabbitmq '{}' +
	fi

	exec su-exec rabbitmq "$BASH_SOURCE" "$@"
fi

# if long and short hostnames are not the same, use long hostnames
if [ -z "${RABBITMQ_USE_LONGNAME:-}" ] && [ "$(hostname)" != "$(hostname -s)" ]; then
	: "${RABBITMQ_USE_LONGNAME:=true}"
fi

exec "$@"
