#!/bin/bash

set -e

# ================



# ================

echo "Mounting the staging area"


# ================

echo "Updating the /etc/fstab for the staging area"

echo "ega_inbox:/ega /ega  nfs  noauto,x-systemd.automount,x-systemd.device-timeout=10,timeo=14,x-systemd.idle-timeout=1min 0 0" >> /etc/fstab

mount -a


# AutoMount points will be created after reboot

# echo "Enabling the ega user to linger"
# loginctl enable-linger ega

echo "Enabling services"

systemctl enable ega-worker.service ega-socket-forwarder.service ega-socket-forwarder.socket

echo "Workers ready"
