#!/bin/bash

set -e

# Some env must be defined
[[ -z "${CEGA_ENDPOINT}" ]] && echo 'Environment CEGA_ENDPOINT is empty' 1>&2 && exit 1
[[ ! -z "${CEGA_USERNAME}" && ! -z "${CEGA_PASSWORD}" ]] && CEGA_ENDPOINT_CREDS="${CEGA_USERNAME}:${CEGA_PASSWORD}"
[[ -z "${CEGA_ENDPOINT_CREDS}" ]] && echo 'Environment CEGA_ENDPOINT_CREDS is empty' 1>&2 && exit 1
# Check if set
[[ -z "${CEGA_ENDPOINT_JSON_PREFIX+x}" ]] && echo 'Environment CEGA_ENDPOINT_JSON_PREFIX must be set' 1>&2 && exit 1

EGA_GID=$(getent group lega | awk -F: '{ print $3 }')

cat > /etc/ega/auth.conf <<EOF
##################
# Central EGA
##################

cega_endpoint_username = ${CEGA_ENDPOINT%/}/%s?idType=username
cega_endpoint_uid = ${CEGA_ENDPOINT%/}/%u?idType=uid
cega_creds = ${CEGA_ENDPOINT_CREDS}
cega_json_prefix = ${CEGA_ENDPOINT_JSON_PREFIX}

##################
# NSS & PAM
##################
#prompt = Knock Knock:
#ega_shell = /bin/bash
#ega_uid_shift = 10000

ega_gid = ${EGA_GID}
chroot_sessions = yes
db_path = /run/ega.db
ega_dir = /ega/inbox
ega_dir_attrs = 2750 # rwxr-s---
#ega_dir_umask = 027 # world-denied
EOF

# Changing permissions
echo "Changing permissions for /ega/inbox"
chgrp lega /ega/inbox
chmod 750 /ega/inbox
chmod g+s /ega/inbox # setgid bit

echo "Starting the FileSystem listener"
gosu lega ega-notifications &

echo "Starting the SFTP server"
exec /opt/openssh/sbin/ega -D -e -f /etc/ega/sshd_config
