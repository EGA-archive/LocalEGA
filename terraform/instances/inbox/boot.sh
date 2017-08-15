#!/bin/bash

set -e

mkfs -t btrfs /dev/vdb
mkdir -m 0700 /ega
chown -R ega:ega /ega
mount /dev/vdb /ega
echo '/dev/vdb /ega btrfs defaults 0 0' >> /etc/fstab

# Creating NFS share (accessible by the EGA user)
mkdir -p /ega/{inbox,staging}
chmod -R 0711 /ega/{inbox,staging} # +x to make su work
chown -R ega:ega /ega/{inbox,staging}
chmod g+s /ega/{inbox,staging}

# ================
yum -y install nfs-utils

:> /etc/exports
echo "/ega/staging $1(rw,sync,no_root_squash,no_all_squash,no_subtree_check)" >> /etc/exports
echo "/ega/inbox $1(rw,sync,no_root_squash,no_all_squash,no_subtree_check)" >> /etc/exports
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
