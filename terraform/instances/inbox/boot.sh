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

sed -i -e "/UMASK/ d" /etc/login.defs
echo "UMASK 022" >> /etc/login.defs

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
# sshd_config

mkdir -p /etc/ssh/authorized_keys

cat > /etc/ssh/sshd_config <<EOF
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

AuthorizedKeysFile .ssh/authorized_keys
SyslogFacility AUTHPRIV

# Fixing path for authorized keys,
# due to root ownership on user's home folder

UsePAM yes
# Not supported on RedHat

# Faster connection
UseDNS no

# Limited access
PermitRootLogin no
X11Forwarding no
AllowTcpForwarding no
PermitTunnel no
PasswordAuthentication no
ChallengeResponseAuthentication no
GSSAPIAuthentication yes
GSSAPICleanupCredentials no

UsePrivilegeSeparation sandbox

AcceptEnv LANG LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES
AcceptEnv LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT
AcceptEnv LC_IDENTIFICATION LC_ALL LANGUAGE
AcceptEnv XMODIFIERS

# Force sftp and chroot jail
#Subsystem sftp  /usr/libexec/openssh/sftp-server
Subsystem sftp internal-sftp

# Force sftp and chroot jail (for all but root)
MATCH GROUP sftp_users
  AuthorizedKeysFile /etc/ssh/authorized_keys/%u
  PasswordAuthentication yes
  ChrootDirectory %h
  # -d (remote start directory relative user root)
  ForceCommand internal-sftp -d /inbox
EOF

systemctl restart sshd
