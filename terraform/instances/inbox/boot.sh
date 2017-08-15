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
sed -i '/^ENCRYPT_METHOD/c\ENCRYPT_METHOD SHA512' /etc/login.defs
sed -i '/^MD5_CRYPT_ENAB/c\MD5_CRYPT_ENAB no' /etc/login.defs

cat > /usr/local/bin/ega_userdel <<'EOF'
#!/bin/bash

# Check for the required argument.
if [ $# != 1 ]; then
    echo "Usage: $0 username"
    exit 1
fi

# Remove cron jobs.
crontab -r -u $1

# Remove at jobs.
# Note that it will remove any jobs owned by the same UID,
# even if it was shared by a different username.
AT_SPOOL_DIR=/var/spool/cron/atjobs
find $AT_SPOOL_DIR -name "[^.]*" -type f -user $1 -delete \;

# Remove the home, cuz owned by root
user_home=$(getent passwd $1 | cut -d: -f6)
if [ "$user_home" == "/ega/inbox/*" ]; then
    rm -rf "$user_home"
fi

# All done.
exit 0
EOF
chmod +x /usr/local/bin/ega_userdel

sed -i '/^USERDEL_CMD/c\USERDEL_CMD /usr/local/bin/ega_userdel' /etc/login.defs

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

cat > /etc/ega-banner <<EOF
Welcome to Local EGA (Sweden)
EOF

cat > /etc/ssh/sshd_config <<EOF
Banner /etc/ega-banner
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

AuthorizedKeysFile .ssh/authorized_keys
SyslogFacility AUTHPRIV

# Fixing path for authorized keys,
# due to root ownership on user's home folder

UsePAM yes

# Faster connection
UseDNS no

# Limited access
PermitRootLogin no
X11Forwarding no
AllowTcpForwarding no
#AllowStreamLocalForwarding no
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
