#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
#setsebool -P ssh_chroot_rw_homedirs on

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

# ================
# Mounting the volume
mkfs -t btrfs -f /dev/vdb # forcing it

rm -rf /ega
mkdir -m 0755 /ega # owned by root

echo "/dev/vdb /ega btrfs defaults 0 0" >> /etc/fstab
mount /ega

chown root:ega /ega
chmod g+s /ega

mkdir -m 0755 /ega/{inbox,staging}
chown root:ega /ega/{inbox,staging}
chmod g+s /ega/{inbox,staging} # setgid bit

sed -i '/^UMASK/c\UMASK 022' /etc/login.defs
#sed -i '/^ENCRYPT_METHOD/c\ENCRYPT_METHOD SHA512' /etc/login.defs
# overrides MD5_CRYPT_ENAB

# ================
# NFS configuration
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

# # ========================
# # ProFTPd
# echo "ProFTPd"
# yum install -y proftpd proftpd-utils

# echo "PassivePorts    6000    6100" >> /etc/proftpd.conf
# setsebool -P allow_ftpd_full_access=1

# # Generating the FTP certificate for TLS encryption
# openssl req -subj "/C=SE/L=Uppsala/O=NBIS/OU=System Developers/emailAddress=ega@nbis.se" \
# -x509 -nodes -newkey rsa:4096 -keyout /etc/pki/tls/certs/proftpd.pem -out /etc/pki/tls/certs/proftpd.pem

# chmod  0440 /etc/pki/tls/certs/proftpd.pem

# # Chrooting the users
# sed -i '/DefaultRoot/c\DefaultRoot ~/inbox ega_users,!adm' /etc/proftpd.conf
# sed -i '/^PROFTPD_OPTIONS/c\PROFTPD_OPTIONS="-DTLS"' /etc/sysconfig/proftpd

# systemctl restart proftpd.service
# systemctl enable proftpd.service


# ========================
# sshd_config

mkdir -p /etc/ssh/authorized_keys

cat > /ega/banner <<EOF
Welcome to Local EGA (Sweden)
EOF


cat > /etc/ssh/sshd_config <<EOF
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key
SyslogFacility AUTHPRIV
# Authentication
UsePAM yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no
ChallengeResponseAuthentication yes
KerberosAuthentication no
GSSAPIAuthentication no
GSSAPICleanupCredentials no
# Faster connection
UseDNS no
# Limited access
AllowGroups ega ega_users
PermitRootLogin no
X11Forwarding no
AllowTcpForwarding no
PermitTunnel no
UsePrivilegeSeparation sandbox
AcceptEnv LANG LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES
AcceptEnv LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT
AcceptEnv LC_IDENTIFICATION LC_ALL LANGUAGE
AcceptEnv XMODIFIERS
# ===========================
# Force sftp and chroot jail
# ===========================
Subsystem sftp internal-sftp
# Force sftp and chroot jail (for users in the ega_users group, but not ega)
MATCH GROUP ega_users
  Banner /ega/banner
  #AuthorizedKeysFile /etc/ssh/authorized_keys/%u
  # Fixing path for authorized keys,
  # due to root ownership on user's home folder
  #AuthenticationMethods publickey,keyboard-interactive
  ChrootDirectory %h
  # -d (remote start directory relative user root)
  ForceCommand internal-sftp -d /inbox
EOF

systemctl restart sshd
