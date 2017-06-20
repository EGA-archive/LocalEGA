#!/bin/bash

set -e

pip install -e /root/ega

sleep 6

# Start the connection to CentralEGA
ega-connect --from-domain cega.broker --from-queue queue --to-domain local.broker --to-exchange exchange --to-routing-key routing_todo --transform set_file_id &
ega-connect --from-domain cega.broker --from-queue users_queue --to-domain local.broker --to-exchange exchange --to-routing-key routing_user --transform set_user_id &

ega-connect --from-domain local.broker --from-queue verified_queue --to-domain cega.broker --to-exchange exchange --to-routing-key routing_to &

exec ega-connect --from-domain local.broker --from-queue account_queue --to-domain cega.broker --to-exchange exchange --to-routing-key users_routing_to
