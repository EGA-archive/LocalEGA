#!/bin/bash

set -e

# ========================
# Disabling the print statement
pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

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

# ========================
# sshd_config

cat > /usr/local/bin/ega-ssh-keys.sh <<'EOF'
#!/bin/bash
eid=$${1%%@*} # strip what's after the @ symbol
query="SELECT pubkey from users where elixir_id = '$${eid}' LIMIT 1"
PGPASSWORD=${db_password} psql -tqA -U postgres -h ega-db -d lega -c "$${query}"
EOF
chown root:ega /usr/local/bin/ega-ssh-keys.sh
chmod 750 /usr/local/bin/ega-ssh-keys.sh

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
AllowGroups ega
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
# Force sftp and chroot jail (for users in the ega group, but not ega)
MATCH GROUP ega USER *,!ega
  Banner /ega/banner
  ChrootDirectory %h
  AuthorizedKeysCommand /usr/local/bin/ega-ssh-keys.sh
  AuthorizedKeysCommandUser ega
  AuthenticationMethods "publickey" "keyboard-interactive:pam"
  # -d (remote start directory relative user root)
  ForceCommand internal-sftp -d /inbox
EOF

systemctl restart sshd


# ========================
# NSS and PAM code

# First, we'll need the pgsql command tool and the libpq-fe.h header
yum -y install postgresql-devel
# yum -y install https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-redhat96-9.6-3.noarch.rpm
# yum -y install postgresql96-devel

# Tell the system to look in these locations too
mkdir -p /usr/local/lib/ega
cat > /etc/ld.so.conf.d/ega.conf <<EOF
/usr/local/lib/ega
/usr/local/lib/ega/security
EOF

# Check against the DB on ega-db first
yum -y install automake autoconf libtool libgcrypt libgcrypt-devel pam-devel

############# NSS code

# For the moment, just the auth branch. To be removed
git clone -b auth https://github.com/NBISweden/LocalEGA.git ~/repo
pushd ~/repo/src/auth/nss
make
make install
cat > /usr/local/etc/nss-ega.conf <<EOF
connection = host=ega-db port=5432 dbname=lega user=postgres password=${db_password} connect_timeout=1 sslmode=disable

##################
# Queries
##################
getpwnam = SELECT elixir_id,'x',$(id -u ega),$(id -g ega),'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users WHERE elixir_id = \$1 LIMIT 1

getpwuid = SELECT elixir_id,'x',$(id -u ega),$(id -g ega),'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users WHERE elixir_id = \$1 LIMIT 1

getspnam = SELECT elixir_id,password_hash,'','','','','','','' FROM users WHERE elixir_id = \$1 LIMIT 1

getpwent = SELECT elixir_id,'x',$(id -u ega),$(id -g ega),'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users

getspent = SELECT elixir_id,password_hash,'','','','','','','' FROM users LIMIT 1
EOF
chown root:root /usr/local/etc/nss-ega.conf
chmod 600 /usr/local/etc/nss-ega.conf
popd

############# PAM code
git clone https://github.com/pam-pgsql/pam-pgsql.git ~/pam-pgsql
pushd ~/pam-pgsql
./autogen.sh
./configure --libdir=/usr/local/lib/ega
make
make install
popd

# Skeleton (with setgid permissions) for the homedir
rm -rf /ega/skel
mkdir -p /ega/skel/inbox && \
chmod 750 /ega/skel/inbox && \
chmod g+s /ega/skel/inbox # rwxr-s---

cp /etc/pam.d/sshd /etc/pam.d/sshd.bak

cat > /etc/pam.d/ega <<EOF
#%PAM-1.0
auth       sufficient   /usr/local/lib/ega/security/pam_pgsql.so
account    sufficient   /usr/local/lib/ega/security/pam_pgsql.so
password   sufficient   /usr/local/lib/ega/security/pam_pgsql.so
#session    optional     pam_echo.so file=/ega/login.msg
session    sufficient   /usr/local/lib/ega/security/pam_pgsql.so
session    required     pam_mkhomedir.so skel=/ega/skel/ umask=0022
EOF

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

cat > /etc/pam_pgsql.conf <<EOF
database=lega
table=users
host=ega-db
port=5432
user=postgres
password=${db_password}
debug=1
pw_type=crypt_sha512
timeout=15
sslmode=disable
pwd_column=password_hash
table=users
user_column=elixir_id
EOF

# Update the ld cache.
# Important to find the libs in /usr/local/lib/ega
ldconfig -v
# it will create the necessary links.

# Update the Name Service Switch, for users and passwords
cp /etc/nsswitch.conf /etc/nsswitch.conf.bak
sed -i -e 's/^passwd:\(.*\)files/passwd:\1ega files/' /etc/nsswitch.conf
sed -i -e 's/^shadow:\(.*\)files/shadow:\1ega files/' /etc/nsswitch.conf

################################################################################
# Temporary test users
PGPASSWORD=${db_password} psql -U postgres -h ega-db -d lega <<-'EOSQL'
SELECT insert_user('fred', '$6$jEcri8b7b5cEReYe$lqJcpzjDpSWNMDwD87h8MAgNg90rgtJknbqeUtonGCW9yTpEVc/LSlESwV8.0zBN4cnk5noiKLodMv/UMwnxM.', 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCcLiS1a/+ul3LOGsBvprYLk1a8XYx6isqkVXQ05PlPLOOs83Qv9aN+uh8YOaebPYK3qlXEH4Tbmk/WJTgJJVkhefNZK+Stk3Pkk6oUqwHfZ7+lDWCqP7/Cvm4+HvVsAO+HBhv/8AhKxk6AI7X0ongrWhJLLJDuraFEYmswKAJOWiuxyKM9EbmmAhocKEx9cUHxnj8Rr3EGJ9urCwQxAIclZUfB5SqHQaGv6ApmVs5S2x6F3RG6upx6eXop4h357psaH7HTi90u6aLEjNf3uYdoCyh8AphqZ6NDVamUCXciO+1jKV03gDBC7xuLCk4ZCF0uRMXoFTmmr77AL33LuysL fred@snic-cloud');
SELECT insert_user('fred2@elixir-europe.org', '$6$jEcri8b7b5cEReYe$lqJcpzjDpSWNMDwD87h8MAgNg90rgtJknbqeUtonGCW9yTpEVc/LSlESwV8.0zBN4cnk5noiKLodMv/UMwnxM.', '' );
EOSQL

mkdir -p /ega/inbox/fred{,2}/inbox
chown ega:ega /ega/inbox/fred{,2}/inbox

