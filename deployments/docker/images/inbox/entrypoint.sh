#!/bin/bash

set -e

# DB_INSTANCE env must be defined
[[ -z "${DB_INSTANCE}" ]] && echo 'Environment DB_INSTANCE is empty' 1>&2 && exit 1

EGA_DB_IP=$(getent hosts ${DB_INSTANCE} | awk '{ print $1 }')
EGA_ID=$(id -u ega)
EGA_GROUP=$(id -g ega)

cat > /etc/ega/auth.conf <<EOF
debug = ok_why_not

##################
# Databases
##################
db_connection = host=${EGA_DB_IP} port=5432 dbname=lega user=${POSTGRES_USER} password=${POSTGRES_PASSWORD} connect_timeout=1 sslmode=disable

enable_cega = yes
cega_endpoint = ${CEGA_ENDPOINT}
cega_user = ${CEGA_ENDPOINT_USER}
cega_password = ${CEGA_ENDPOINT_PASSWORD}
cega_resp_passwd = ${CEGA_ENDPOINT_RESP_PASSWD}
cega_resp_pubkey = ${CEGA_ENDPOINT_RESP_PUBKEY}

##################
# NSS & PAM Queries
##################
get_ent = SELECT elixir_id FROM users WHERE elixir_id = $1 LIMIT 1
add_user = SELECT insert_user($1,$2,$3)
get_password = SELECT password_hash FROM users WHERE elixir_id = $1 LIMIT 1
get_account = SELECT elixir_id FROM users WHERE elixir_id = $1 and current_timestamp < last_accessed + expiration

#prompt = Knock Knock:

ega_uid = 1000
ega_gid = 1000
ega_gecos = EGA User
ega_shell = /sbin/nologin

##################
# FUSE mount
##################
ega_fuse_dir = /lega
ega_fuse_exec = /usr/bin/ega-fs
ega_fuse_flags = nodev,noexec,uid=1000,gid=1000,suid

ega_dir = /ega/inbox
ega_dir_attrs = 2750 # rwxr-s---
EOF

cat > /usr/local/bin/ega_ssh_keys.sh <<EOF
#!/bin/bash

eid=\${1%%@*} # strip what's after the @ symbol

query="SELECT pubkey from users where elixir_id = '\${eid}' LIMIT 1"

PGPASSWORD=${POSTGRES_PASSWORD} psql -tqA -U ${POSTGRES_USER} -h ${DB_INSTANCE} -d lega -c "\${query}"
EOF
chmod 750 /usr/local/bin/ega_ssh_keys.sh
chgrp ega /usr/local/bin/ega_ssh_keys.sh

# Greetings per site
[[ -z "${LEGA_GREETINGS}" ]] || echo ${LEGA_GREETING} > /ega/banner

# Changing permissions
echo "Changing permissions for /ega/inbox"
chown root:ega /ega/inbox
chmod 750 /ega/inbox
chmod g+s /ega/inbox # setgid bit

# Start cronie
echo "Starting cron"
cat > /usr/local/bin/fuse_cleanup.sh <<EOF
#!/bin/bash

set -e

for mnt in $1/*
do
    { umount $mnt &>/dev/null && rmdir $mnt; } || :
done
EOF
chmod 750 /usr/local/bin/fuse_cleanup.sh

cat > /etc/crontab <<EOF
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed

*/5 * * * * root /usr/local/bin/fuse_cleanup.sh /lega
EOF
crond -s

echo "Starting the SFTP server"
exec /usr/sbin/sshd -D -e
