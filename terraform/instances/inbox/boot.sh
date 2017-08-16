#!/bin/bash

set -e

setsebool -P ssh_chroot_rw_homedirs on

mkfs -t btrfs -f /dev/vdb # forcing it

rm -rf /ega
mkdir -m 0700 /ega # owned by root

echo "/dev/vdb /ega btrfs defaults 0 0" >> /etc/fstab
mount /ega

chown root:root /ega
chmod 0755 /ega # readable by ega

mkdir -m 0755 /ega/{inbox,staging}
chown root:root /ega/inbox # for chrooting
chown ega:ega /ega/staging

chmod 0755 /ega/{inbox,staging}

sed -i '/^UMASK/c\UMASK 022' /etc/login.defs
#sed -i '/^ENCRYPT_METHOD/c\ENCRYPT_METHOD SHA512' /etc/login.defs
# overrides MD5_CRYPT_ENAB

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
groupadd --system ega_users

# Skeleton for them
#rm -rf /etc/skel/.bash*
mkdir -p /etc/skel/inbox && \
    chmod 700 /etc/skel/inbox

cat > /etc/default/useradd <<EOF
GROUP=ega_users
HOME=/ega/inbox
INACTIVE=-1
EXPIRE=
SHELL=/usr/sbin/nologin
SKEL=/etc/skel
CREATE_MAIL_SPOOL=no
EOF

# ========================
# Only requests from Sweden (or local ones)

cat > /etc/hosts.allow <<EOF
sshd: 192.168.10.     : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed local)")&  : ALLOW
sshd: .se             : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed .se)")&    : ALLOW
ALL : ALL             : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (denied)")&         : DENY
EOF

# # ========================
# # Fail2Ban

# yum -y install fail2ban
# systemctl enable fail2ban
# systemctl restart fail2ban

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config

# ========================
# ProFTPd
echo "ProFTPd"
yum install -y proftpd proftpd-utils

echo "PassivePorts    6000    6100" >> /etc/proftpd.conf
setsebool -P allow_ftpd_full_access=1

# Generating the FTP certificate for TLS encryption
openssl req -subj "/C=SE/L=Uppsala/O=NBIS/OU=System Developers/emailAddress=ega@nbis.se" \
-x509 -nodes -newkey rsa:4096 -keyout /etc/pki/tls/certs/proftpd.pem -out /etc/pki/tls/certs/proftpd.pem

chmod  0440 /etc/pki/tls/certs/proftpd.pem

# Chrooting the users
sed -i '/DefaultRoot/c\DefaultRoot ~/inbox ega_users,!adm' /etc/proftpd.conf
sed -i '/^PROFTPD_OPTIONS/c\PROFTPD_OPTIONS="-DTLS"' /etc/sysconfig/proftpd

systemctl restart proftpd.service
systemctl enable proftpd.service


