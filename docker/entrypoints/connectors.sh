#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

# CentralEGA to LocalEGA
ega-connect --from-domain cega.broker --from-queue queue --to-domain local.broker --to-exchange exchange --to-routing-key routing_todo --transform set_file_id &
ega-connect --from-domain cega.broker --from-queue users_queue --to-domain local.broker --to-exchange exchange --to-routing-key routing_user --transform set_user_id &

# LocalEGA to CentralEGA
ega-connect --from-domain local.broker --from-queue verified_queue --to-domain cega.broker --to-exchange exchange --to-routing-key routing_to &
ega-connect --from-domain local.broker --from-queue account_queue --to-domain cega.broker --to-exchange exchange --to-routing-key users_routing_to

wait
