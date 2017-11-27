#!/bin/bash

set -e

# ================

git clone https://github.com/NBISweden/LocalEGA.git ~/repo
pip3.6 install ~/repo/src

# ================

echo "Mounting the staging area"
mount -t nfs ega-inbox:/ega /ega || exit 1

# ================

echo "Updating the /etc/fstab for the staging area"
sed -i -e '/ega-inbox:/ d' /etc/fstab
echo "ega-inbox:/ega /ega  nfs  noauto,x-systemd.automount,x-systemd.device-timeout=10,timeo=14,x-systemd.idle-timeout=1min 0 0" >> /etc/fstab
# AutoMount points will be created after reboot

# echo "Enabling the ega user to linger"
# loginctl enable-linger ega

echo "Enabling services"
systemctl start ega-worker.service ega-socket-forwarder.service ega-socket-forwarder.socket
systemctl enable ega-worker.service ega-socket-forwarder.service ega-socket-forwarder.socket

echo "Workers ready"
