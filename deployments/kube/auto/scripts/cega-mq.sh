#!/bin/bash

set -e

# Initialization
rabbitmq-plugins enable --offline rabbitmq_federation
rabbitmq-plugins enable --offline rabbitmq_federation_management
rabbitmq-plugins enable --offline rabbitmq_shovel
rabbitmq-plugins enable --offline rabbitmq_shovel_management

cp --remove-destination /temp/rabbitmq.config /etc/rabbitmq/rabbitmq.config
cp --remove-destination /temp/defs.json /etc/rabbitmq/defs.json
chmod 640 /etc/rabbitmq/rabbitmq.config
chmod 640 /etc/rabbitmq/defs.json

exec rabbitmq-server
