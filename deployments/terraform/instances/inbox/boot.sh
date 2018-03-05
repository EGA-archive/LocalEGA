#!/bin/bash

cidr=$1

yum -y install automake autoconf libtool libgcrypt libgcrypt-devel postgresql-devel pam-devel libcurl-devel jq-devel nfs-utils fuse fuse-libs cronie
echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf


modprobe fuse
mkdir -p /mnt/lega
mkfs -t btrfs -f /dev/vdb

systemctl start ega.mount
systemctl enable ega.mount

# for the ramfs cache
mkdir -p /ega/cache
sed -i -e '/ega/ d' /etc/fstab
echo "ramfs /ega/cache ramfs   size=200m 0 0" >> /etc/fstab
mount /ega/cache


mkdir -p /ega/{inbox,staging}
chown root:ega /ega/inbox
chown ega:ega /ega/staging
chmod 0750 /ega/{inbox,staging}
chmod g+s /ega/{inbox,staging}
echo "/ega/inbox   ${cidr}(rw,sync,no_root_squash,no_all_squash,no_subtree_check)" > /etc/exports
echo "/ega/staging ${cidr}(rw,sync,no_root_squash,no_all_squash,no_subtree_check)" >> /etc/exports
systemctl restart rpcbind nfs-server nfs-lock nfs-idmap
systemctl enable rpcbind nfs-server nfs-lock nfs-idmap

git clone https://github.com/NBISweden/LocalEGA-auth.git ~/repo && cd ~/repo/src && make install && ldconfig -v

pip3.6 uninstall -y lega
pip3.6 install pika==0.11.0 fusepy
pip3.6 install git+https://github.com/NBISweden/LocalEGA.git@feature/pgp

cp /etc/nsswitch.conf /etc/nsswitch.conf.bak
sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf

cp /usr/sbin/sshd /usr/sbin/ega
cat > /etc/pam.d/ega <<EOF
#%PAM-1.0
auth       requisite    /usr/local/lib/ega/pam_ega.so
account    requisite    /usr/local/lib/ega/pam_ega.so
password   required     pam_deny.so
session    requisite    /usr/local/lib/ega/pam_ega.so
EOF
cat > /etc/ega/config <<EOF
Port 9000
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key
SyslogFacility AUTHPRIV
# Authentication
UsePAM yes
AuthenticationMethods "publickey" "keyboard-interactive:pam"
PubkeyAuthentication yes
PasswordAuthentication no
ChallengeResponseAuthentication yes
KerberosAuthentication no
GSSAPIAuthentication no
GSSAPICleanupCredentials no
# Faster connection
UseDNS no
# Limited access
DenyGroups *,!ega
DenyUsers root ega
PermitRootLogin no
X11Forwarding no
AllowTcpForwarding no
PermitTunnel no
UsePrivilegeSeparation sandbox
AcceptEnv LANG LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES
AcceptEnv LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT
AcceptEnv LC_IDENTIFICATION LC_ALL LANGUAGE
AcceptEnv XMODIFIERS
Subsystem sftp internal-sftp
Banner /ega/banner
AuthorizedKeysCommand /usr/local/bin/ega_ssh_keys
AuthorizedKeysCommandUser root
EOF
chmod 644 /etc/ega/config

cat > /etc/hosts.allow <<EOF
sshd: 192.168.10.0/24 : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed local)")&    : ALLOW
sshd: 84.88.66.194    : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed fred@crg)")& : ALLOW
sshd: .se             : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed .se)")&      : ALLOW
ega: 84.88.66.194    : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed fred@crg)")& : ALLOW
ega: .se             : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (allowed .se)")&      : ALLOW
ALL : ALL             : spawn (/usr/bin/logger -i -p authpriv.info "%d[%p]\: %h (denied)")&           : DENY
EOF

echo "Starting the SFTP server"
systemctl start ega-inbox.service
systemctl enable ega-inbox.service

cat > /usr/local/bin/fuse_cleanup.sh <<'EOF'
#!/bin/bash
set -e

for mnt in $1/*
do
    { umount ${mnt} &>/dev/null && rmdir ${mnt}; } || :
done
EOF
chmod 750 /usr/local/bin/fuse_cleanup.sh

echo '*/5 * * * * root /usr/local/bin/fuse_cleanup.sh /lega' >> /etc/crontab
systemctl start crond.service
systemctl enable crond.service



