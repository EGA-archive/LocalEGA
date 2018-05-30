#!/bin/bash

set -e

# DB_INSTANCE env must be defined
[[ -z "${DB_INSTANCE}" ]] && echo 'Environment DB_INSTANCE is empty' 1>&2 && exit 1

# [[ -z "${MQ_INSTANCE}" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && exit 1
# echo "Waiting for Local Message Broker"
# until nc -4 --send-only ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

EGA_DB_IP=$(getent hosts ${DB_INSTANCE} | awk '{ print $1 }')
EGA_UID=$(id -u ega)
EGA_GID=$(id -g ega)

cat > /etc/ega/auth.conf <<EOF
enable_cega = yes
cega_endpoint = ${CEGA_ENDPOINT}
cega_creds = ${CEGA_ENDPOINT_CREDS}
cega_json_passwd = ${CEGA_ENDPOINT_JSON_PASSWD}
cega_json_pubkey = ${CEGA_ENDPOINT_JSON_PUBKEY}

##################
# NSS & PAM
##################
# prompt = Knock Knock:
ega_uid = ${EGA_UID}
ega_gid = ${EGA_GID}
# ega_gecos = EGA User
# ega_shell = /sbin/nologin

ega_dir = /ega/inbox
ega_dir_attrs = 2750 # rwxr-s---

##################
# FUSE mount
##################
ega_fuse_dir = /lega
ega_fuse_exec = /usr/bin/ega-fs
ega_fuse_flags = nodev,noexec,uid=${EGA_UID},gid=${EGA_GID},suid

EOF

# for the ramfs cache
mkdir -p /ega/cache
sed -i -e '/ega/ d' /etc/fstab
echo "ramfs /ega/cache ramfs   size=200m 0 0" >> /etc/fstab
mount /ega/cache

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

for mnt in \$1/*
do
    { umount \${mnt} &>/dev/null && rmdir \${mnt}; } || :
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
exec /usr/sbin/ega -D -e -f /etc/ega/sshd_config
