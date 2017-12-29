#!/bin/bash

set -e

# DB_INSTANCE env must be defined
[[ -z "${DB_INSTANCE}" ]] && echo 'Environment DB_INSTANCE is empty' 1>&2 && exit 1

chown root:ega /ega/inbox
chmod 750 /ega/inbox
chmod g+s /ega/inbox # setgid bit

EGA_DB_IP=$(getent hosts ${DB_INSTANCE} | awk '{ print $1 }')

cat > /etc/ega/auth.conf <<EOF
debug = ok_why_not

##################
# Databases
##################
db_connection = host=${EGA_DB_IP} port=5432 dbname=lega user=${POSTGRES_USER} password=${POSTGRES_PASSWORD} connect_timeout=1 sslmode=disable

enable_rest = yes
rest_endpoint = ${CEGA_ENDPOINT}
rest_user = ${CEGA_ENDPOINT_USER}
rest_password = ${CEGA_ENDPOINT_PASSWORD}
rest_resp_passwd = ${CEGA_ENDPOINT_RESP_PASSWD}
rest_resp_pubkey = ${CEGA_ENDPOINT_RESP_PUBKEY}

##################
# NSS Queries
##################
nss_get_user = SELECT elixir_id,'x',1000,1000,'EGA User','/mnt/lega/'|| elixir_id,'/sbin/nologin' FROM users WHERE elixir_id = \$1 LIMIT 1
nss_add_user = SELECT insert_user(\$1,\$2,\$3)

##################
# PAM Queries
##################
pam_auth = SELECT password_hash FROM users WHERE elixir_id = \$1 LIMIT 1
pam_acct = SELECT elixir_id FROM users WHERE elixir_id = \$1 and current_timestamp < last_accessed + expiration
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

# Starting the FUSE layer
sed -i -e '/lega:/ d' /etc/fstab
echo "/usr/bin/ega-fs /mnt/lega fuse allow_other,gid=0,rootdir=/ega/inbox 0 0" >> /etc/fstab # no foreground!
mount -a

echo "Starting the SFTP server"
exec /usr/sbin/sshd -D -e
