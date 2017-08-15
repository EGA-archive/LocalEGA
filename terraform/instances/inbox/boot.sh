#!/bin/bash

set -e

mkfs -t btrfs -f /dev/vdb # forcing it

rm -rf /ega && mkdir /ega

echo "/dev/vdb /ega btrfs defaults 0 0" >> /etc/fstab
mount /ega

chown -R ega:ega /ega
chmod 0700 /ega

# ================
yum -y install nfs-utils

:> /etc/exports
echo "/ega $1(rw,sync,no_root_squash,no_all_squash,no_subtree_check)" >> /etc/exports
#exportfs -ra

systemctl enable rpcbind
systemctl enable nfs-server
systemctl enable nfs-lock
systemctl enable nfs-idmap

systemctl restart rpcbind
systemctl restart nfs-server
systemctl restart nfs-lock
systemctl restart nfs-idmap

# ================
# Group for newly created users (Local EGA users)
groupadd --system sftp_users

# Skeleton for them
#rm -rf /etc/skel/.bash*
mkdir -p /etc/skel/inbox && \
    chmod 700 /etc/skel/inbox

cat > /etc/default/useradd <<EOF
GROUP=sftp_users
HOME=/ega/inbox
INACTIVE=-1
EXPIRE=
SHELL=/usr/sbin/nologin
SKEL=/etc/skel
CREATE_MAIL_SPOOL=no
EOF
