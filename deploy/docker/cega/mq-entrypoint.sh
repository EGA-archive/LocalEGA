#!/usr/bin/env bash

set -eo pipefail

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
  "parameters": [],
  "policies": [],
  "queues": [
    {"name": "from_fega", "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}}
  ],
  "exchanges": [
    {"name":"cega", "vhost":"/", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{}}
  ], 
  "bindings": [
    { "source":"cega", "vhost": "/", "destination":"from_fega", "destination_type":"queue", "routing_key":"#", "arguments":{}}
  ]
}
EOF

chown rabbitmq:rabbitmq /etc/rabbitmq/definitions.json
chown rabbitmq:rabbitmq /etc/rabbitmq/rabbitmq.conf

chmod 600 /etc/rabbitmq/definitions.json
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
