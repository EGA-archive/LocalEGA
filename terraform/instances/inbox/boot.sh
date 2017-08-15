#!/bin/bash

set -e

# ================
yum -y install nfs-utils

# Creating NFS share (accessible by root)
mkdir -p -m 0700 /ega/{inbox,staging}

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
# Do the rest as the EGA user
su -c '/home/ega/boot.sh' - ega

