#!/bin/bash
chown rabbitmq:rabbitmq /etc/rabbitmq/*
find /var/lib/rabbitmq \! -user rabbitmq -exec chown rabbitmq '{}' +
exec docker-entrypoint.sh rabbitmq-server
