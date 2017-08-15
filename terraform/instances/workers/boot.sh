#!/bin/bash

set -e

# ================

echo "Mounting the staging area"
mkdir -p -m 0700 /ega/{inbox,staging}
mount -t nfs ega-inbox:/ega/staging /ega/staging || exit 1
mount -t nfs ega-inbox:/home /ega/inbox || exit 1

echo "Updating the /etc/fstab for the staging area"
sed -i -e '/ega-inbox:/ d' /etc/fstab
echo "ega-inbox:/ega/staging /ega/staging  nfs   auto,noatime,nolock,bg,nfsvers=4,intr,tcp,actimeo=1800 0 0" >> /etc/fstab
echo "ega-inbox:/home /ega/inbox  nfs   auto,noatime,nolock,bg,nfsvers=4,intr,tcp,actimeo=1800 0 0" >> /etc/fstab


# ================
# Do the rest as the EGA user
su - ega

unzip /tmp/gpg.zip -d ~/.gnupg && \
rm /tmp/gpg.zip

mkdir -p -m 0700 ~/.rsa && \
unzip /tmp/rsa.zip -d ~/.rsa && \
rm /tmp/rsa.zip

mkdir -p -m 0700 /etc/ega && \
unzip /tmp/certs.zip -d ~/certs && \
rm /tmp/certs.zip

git clone https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done


echo "Waiting for GPG and SSH agent"
until nc -4 --send-only ega-keys 9010 </dev/null &>/dev/null; do sleep 1; done
echo "Starting the gpg-agent forwarder"
ega-socket-forwarder ~/.gnupg/S.gpg-agent \
		     ega-keys:9010 \
		     --certfile ~/certs/selfsigned.cert &

echo "Starting the worker"
ega-worker &


