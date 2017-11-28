#!/bin/bash

set -e

# # ========================
# # Fail2Ban

# yum -y install fail2ban
# systemctl enable fail2ban
# systemctl restart fail2ban

# ================
# Mounting the volume

rm -rf /ega
mkdir -m 0755 /ega # owned by root

mkfs -t btrfs -f /dev/vdb # forcing it

echo "/dev/vdb /ega btrfs defaults 0 0" >> /etc/fstab
mount /ega

chown root:ega /ega
chmod g+s /ega

mkdir -m 0755 /ega/{inbox,staging}
chown root:ega /ega/{inbox,staging}
chmod g+s /ega/{inbox,staging} # setgid bit

# ================
# NFS configuration
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

# ========================
# NSS and PAM code
cp /etc/pam.d/sshd /etc/pam.d/sshd.bak
cat > /etc/pam.d/sshd <<EOF
#%PAM-1.0
auth       include      ega
auth       include      sshd.bak
account    include      ega
account    include      sshd.bak
password   include      ega
password   include      sshd.bak
session    include      ega
session    include      sshd.bak
EOF

# Update the ld cache.
# Important to find the libs in /usr/local/lib/ega

# Update the Name Service Switch, for users and passwords
cp /etc/nsswitch.conf /etc/nsswitch.conf.bak
sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf

# Reverting
sed -i -e "s/name:\sega/name: centos/" /etc/cloud/cloud.cfg
sed -i -e "s/gecos:.*/gecos: Centos User/" /etc/cloud/cloud.cfg
systemctl reboot
