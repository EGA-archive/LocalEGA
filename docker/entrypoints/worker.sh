#!/bin/bash

set -e

pip install -e /root/ega

cat /root/.ssh/ega.pub >> /root/.ssh/authorized_keys && \
chmod 600 /root/.ssh/authorized_keys

# cat > /root/.gnupg/gpg-agent.conf <<EOF
# #extra-socket /root/.gnupg/S.ega
# EOF

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for GPG and SSH agent"
until nc -4 --send-only ega-keys 9010 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the worker"
#exec ega-worker
exec ega-gpg-forwarder
