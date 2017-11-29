#!/usr/bin/env bash
#set -e

USER=cega_$1
PASSWORD=$2
VHOST=$1

# Get RabbitMQadmin
[[ -x /usr/local/bin/rabbitmqadmin ]] || {
    curl -o /usr/local/bin/rabbitmqadmin https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/rabbitmq_v3_6_14/bin/rabbitmqadmin
    chmod 755 /usr/local/bin/rabbitmqadmin
}

#rabbitmqctl set_disk_free_limit "1GB"

# Creating VHost
rabbitmqctl add_vhost ${VHOST}

# Adding user
rabbitmqctl add_user ${USER} ${PASSWORD}
rabbitmqctl set_user_tags ${USER} administrator

# Setting permissions
rabbitmqctl set_permissions -p ${VHOST} ${USER} ".*" ".*" ".*"


RABBITMQADMIN="/usr/local/bin/rabbitmqadmin -u ${USER} -p ${PASSWORD}"

# Adding queues
${RABBITMQADMIN} declare queue --vhost=${VHOST} name=${VHOST}.v1.commands.completed durable=true auto_delete=false
${RABBITMQADMIN} declare queue --vhost=${VHOST} name=${VHOST}.v1.commands.file      durable=true auto_delete=false

# Adding exchanges
${RABBITMQADMIN} declare exchange --vhost=${VHOST} name=localega.v1 type=topic durable=true auto_delete=false internal=false

# Adding bindings
${RABBITMQADMIN} --vhost=${VHOST} declare binding destination_type="queue" \
	                                       source=localega.v1 \
	                                       destination=${VHOST}.v1.commands.file \
					       routing_key=${VHOST}.file
${RABBITMQADMIN} --vhost=${VHOST} declare binding destination_type="queue" \
	                                       source=localega.v1 \
	                                       destination=${VHOST}.v1.commands.completed \
					       routing_key=${VHOST}.completed

echo "RabbitMQ settings created for ${VHOST}"
