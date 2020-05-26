#!/bin/bash

[[ -z "${MQ_USER}" ]] && echo 'Environment variable MQ_USER is empty' 1>&2 && exit 1
[[ -z "${MQ_PASSWORD_HASH}" ]] && echo 'Environment variable MQ_PASSWORD_HASH is empty' 1>&2 && exit 1
[[ -z "${CEGA_CONNECTION}" ]] && echo 'Environment variable CEGA_CONNECTION is empty' 1>&2 && exit 1


cat >> /etc/rabbitmq/rabbitmq.conf <<EOF
listeners.ssl.default = 5671
ssl_options.cacertfile = ${MQ_CA:-/etc/rabbitmq/ssl/ca.pem}
ssl_options.certfile = ${MQ_SERVER_CERT:-/etc/rabbitmq/ssl/mq-server.pem}
ssl_options.keyfile = ${MQ_SERVER_KEY:-/etc/rabbitmq/ssl/mq-server-key.pem}
ssl_options.verify = verify_peer
ssl_options.fail_if_no_peer_cert = true
ssl_options.versions.1 = tlsv1.2
disk_free_limit.absolute = 1GB
management.listener.port = 15672
management.load_definitions = /etc/rabbitmq/definitions.json
EOF

chown rabbitmq:rabbitmq /etc/rabbitmq/rabbitmq.conf
chmod 600 /etc/rabbitmq/rabbitmq.conf

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
      "value": { "ack-mode": "on-confirm", "queue": "v1.files", "trust-user-id": false, "uri": "${CEGA_CONNECTION}" }
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
    {"name": "ingest",    "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "verified",  "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "accession", "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "backup1",   "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "backup2",   "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "completed", "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}},
    {"name": "errors",    "vhost": "/", "durable": true, "auto_delete": false, "arguments":{}}
  ],
  "exchanges": [
    {"name":"cega", "vhost":"/", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{}}, 
    {"name":"lega", "vhost":"/", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{}}
  ], 
  "bindings": [
    { "source":"lega", "vhost": "/", "destination":"ingest", "destination_type":"queue", "routing_key":"ingest", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"verified", "destination_type":"queue", "routing_key":"verified", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"accession", "destination_type":"queue", "routing_key":"accession", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"backup1", "destination_type":"queue", "routing_key":"backup1", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"backup2", "destination_type":"queue", "routing_key":"backup2", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"completed", "destination_type":"queue", "routing_key":"completed", "arguments":{}},
    { "source":"lega", "vhost": "/", "destination":"errors", "destination_type":"queue", "routing_key":"error", "arguments":{}}
  ]
}
EOF
chown rabbitmq:rabbitmq /etc/rabbitmq/definitions.json
chmod 600 /etc/rabbitmq/definitions.json

cat > /etc/rabbitmq/advanced.config <<EOF
[
  {rabbit,
    [{tcp_listeners, []}
  ]},
  {rabbitmq_shovel,
    [{shovels, [
      {to_cega,
        [{source,
          [{protocol, amqp091},
            {uris, ["amqp://"]},
            {declarations, [{'queue.declare', [{exclusive, true}]},
              {'queue.bind',
                [{exchange, <<"cega">>},
                  {queue, <<>>},
                  {routing_key, <<"#">>}
                ]}
            ]},
            {queue, <<>>},
            {prefetch_count, 10}
          ]},
          {destination,
            [{protocol, amqp091},
              {uris, ["${CEGA_CONNECTION}"]},
              {declarations, []},
              {publish_properties, [{delivery_mode, 2}]},
              {publish_fields, [{exchange, <<"localega.v1">>}]}]},
          {ack_mode, on_confirm},
          {reconnect_delay, 5}
        ]},
      {cega_completion,
        [{source,
          [{protocol, amqp091},
            {uris, ["amqp://"]},
            {declarations, [{'queue.declare', [{exclusive, true}]},
              {'queue.bind',
                [{exchange, <<"lega">>},
                  {queue, <<>>},
                  {routing_key, <<"completed">>}
                ]}
            ]},
            {queue, <<>>},
            {prefetch_count, 10}
          ]},
          {destination,
            [{protocol, amqp091},
              {uris, ["amqp://"]},
              {declarations, []},
              {publish_properties, [{delivery_mode, 2}]},
              {publish_fields, [{exchange, <<"cega">>},
                {routing_key, <<"files.completed">>}
              ]}
            ]},
          {ack_mode, on_confirm},
          {reconnect_delay, 5}
        ]},
      {cega_verified,
        [{source,
          [{protocol, amqp091},
            {uris, ["amqp://"]},
            {declarations, [{'queue.declare', [{exclusive, true}]},
              {'queue.bind',
                [{exchange, <<"lega">>},
                  {queue, <<>>},
                  {routing_key, <<"verified">>}
                ]}
            ]},
            {queue, <<>>},
            {prefetch_count, 10}
          ]},
          {destination,
            [{protocol, amqp091},
              {uris, ["amqp://"]},
              {declarations, []},
              {publish_properties, [{delivery_mode, 2}]},
              {publish_fields, [{exchange, <<"cega">>},
                {routing_key, <<"files.verified">>}
              ]}
            ]},
          {ack_mode, on_confirm},
          {reconnect_delay, 5}
        ]}
    ]}
  ]}
].
EOF
chown rabbitmq:rabbitmq /etc/rabbitmq/advanced.config
chmod 600 /etc/rabbitmq/advanced.config


# Ownership by 'rabbitmq'
[[ -e "${MQ_CA}" ]] && chown rabbitmq:rabbitmq "${MQ_CA}"
[[ -e "${MQ_SERVER_CERT}" ]] && chown rabbitmq:rabbitmq "${MQ_SERVER_CERT}"
[[ -e "${MQ_SERVER_KEY}" ]] && chown rabbitmq:rabbitmq "${MQ_SERVER_KEY}"
find /var/lib/rabbitmq \! -user rabbitmq -exec chown rabbitmq '{}' +

# Run as 'rabbitmq'
exec su-exec rabbitmq "$@"
