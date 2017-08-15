#!/bin/bash

set -e

# ================

echo "Mounting the staging area"
mkdir -p -m 0700 /ega/{inbox,staging}
chown -R ega:ega /ega/{inbox,staging}
mount -t nfs ega-inbox:/ega/staging /ega/staging || exit 1
mount -t nfs ega-inbox:/ega/inbox /ega/inbox || exit 1

echo "Updating the /etc/fstab for the staging area"
sed -i -e '/ega-inbox:/ d' /etc/fstab
echo "ega-inbox:/ega/staging /ega/staging  nfs   auto,noatime,nolock,bg,nfsvers=4,intr,tcp,actimeo=1800 0 0" >> /etc/fstab
echo "ega-inbox:/ega/inbox /ega/inbox  nfs   auto,noatime,nolock,bg,nfsvers=4,intr,tcp,actimeo=1800 0 0" >> /etc/fstab
