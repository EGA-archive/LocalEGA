#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

# CentralEGA to LocalEGA
ega-connect --transform set_file_id \
	    cega.broker sweden.v1.commands.file \
	    local.broker lega lega.tasks &
ega-connect --transform set_user_id \
	    cega.broker sweden.v1.commands.user \
	    local.broker lega lega.users &

# LocalEGA to CentralEGA
ega-connect local.broker verified \
	    cega.broker localega.v1 sweden.file.completed &
ega-connect local.broker account \
	    cega.broker localega.v1 sweden.user.account &

wait

