#!/usr/bin/env bash

set -e
#set -x

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EGA=$HERE/..
[ -n "$1" ] && [ -d "$1" ] && EGA=$1

function cleanup {
    echo -e "\nStopping background jobs"
    kill -9 -"$$"
    exit 1
}
trap 'cleanup' INT TERM

# NOTE: the ega-inbox, ega-db and ega-mq containers must be already started

echo "Starting EGA in $EGA"
pushd $EGA >/dev/null

# Start the connection to CentralEGA
ega-connect --from-domain cega.broker --from-queue queue --to-domain local.broker --to-exchange exchange --to-routing-key routing_todo --transform set_file_id &
ega-connect --from-domain local.broker --from-queue verified_queue --to-domain cega.broker --to-exchange exchange --to-routing-key routing_to &
ega-connect --from-domain cega.broker --from-queue users_queue --to-domain local.broker --to-exchange exchange --to-routing-key routing_user --transform set_user_id &
ega-connect --from-domain local.broker --from-queue account_queue --to-domain cega.broker --to-exchange exchange --to-routing-key users_routing_to &
# Start the frontend
ega-frontend &
# Start the inbox listener (for user account creation)
#ega-inbox &
# Start the vault listener
ega-vault &
# Start the verification
ega-verify &
# re-start the GPG agent
$EGA/tools/start_agent.sh
# Start 2 workers
source $EGA/private/gpg/agent.env && ega-worker &
source $EGA/private/gpg/agent.env && ega-worker &
# Start the monitors
# ega-monitor --sys &
# ega-monitor --user &

# Run the inbox creation service
docker exec -i ega-inbox ega-inbox &

popd >/dev/null
sleep 3
echo "EGA running..."

# Wait for everyone to finish
wait
