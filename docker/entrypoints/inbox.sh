#!/bin/bash

set -e

chown root:ega /ega/inbox
chmod 750 /ega/inbox
chmod g+s /ega/inbox # setgid bit

pushd /root/ega/auth/nss
make
make install
popd

ldconfig -v

cat > /etc/pam_pgsql.conf <<EOF
database=lega
table=users
host=ega-db
port=5432
user=postgres
password=${POSTGRES_PASSWORD}
debug=1
pw_type=crypt_sha512
timeout=15
sslmode=disable
pwd_column=password_hash
table=users
user_column=elixir_id
EOF

cat > /usr/local/etc/nss-ega.conf <<EOF
connection = host=ega-db port=5432 dbname=lega user=postgres password=${POSTGRES_PASSWORD} connect_timeout=1 sslmode=disable

##################
# Queries
##################
getpwnam = SELECT elixir_id,'x',$(id -u ega),$(id -g ega),'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users WHERE elixir_id = \$1 LIMIT 1

getpwuid = SELECT elixir_id,'x',$(id -u ega),$(id -g ega),'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users WHERE elixir_id = \$1 LIMIT 1

getspnam = SELECT elixir_id,password_hash,'','','','','','','' FROM users WHERE elixir_id = \$1 LIMIT 1

getpwent = SELECT elixir_id,'x',$(id -u ega),$(id -g ega),'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users

getspent = SELECT elixir_id,password_hash,'','','','','','','' FROM users LIMIT 1
EOF


pip install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the inbox listener"
ega-inbox &

echo "Starting the SFTP server"
exec /usr/sbin/sshd -D -e
