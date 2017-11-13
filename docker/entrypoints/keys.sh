#!/bin/bash

set -e

cp -r /root/ega /root/run
pip3.6 install /root/run

GPG=/usr/local/bin/gpg2
GPG_AGENT=/usr/local/bin/gpg-agent
GPG_PRESET=/usr/local/libexec/gpg-preset-passphrase

chmod 700 /root/.gnupg
pkill gpg-agent || true
#/usr/local/bin/gpgconf --kill gpg-agent || true
rm -rf $(gpgconf --list-dirs agent-extra-socket) || true

cat > /root/.gnupg/gpg-agent.conf <<EOF
#log-file gpg-agent.log
allow-preset-passphrase
default-cache-ttl 2592000 # one month
max-cache-ttl 31536000    # one year
pinentry-program /usr/local/bin/pinentry-curses
allow-loopback-pinentry
enable-ssh-support
#extra-socket /run/ega/S.gpg-agent.extra
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF


# Start the GPG Agent in /root/.gnupg
${GPG_AGENT} --daemon
# This should create /run/ega/S.gpg-agent{,.extra,.ssh}

#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(${GPG} -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
${GPG_PRESET} --preset -P $GPG_PASSPHRASE $KEYGRIP
unset GPG_PASSPHRASE

echo "Starting the gpg-agent proxy"
ega-socket-proxy '0.0.0.0:9010' /root/.gnupg/S.gpg-agent --certfile /etc/ega/ssl.cert --keyfile /etc/ega/ssl.key &

echo "Starting the key management server"
exec ega-keyserver --keys /etc/ega/keys.ini
