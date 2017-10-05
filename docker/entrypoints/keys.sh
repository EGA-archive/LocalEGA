#!/bin/bash

set -e

git clone -b docker https://github.com/NBISweden/LocalEGA.git ~/repo
pip3.6 install ~/repo/src

echo "Starting the key management server"
ega-keyserver --keys /etc/ega/keys.ini &

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
/usr/local/bin/gpg-agent --daemon
# This should create /run/ega/S.gpg-agent{,.extra,.ssh}

#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(/usr/local/bin/gpg -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
/usr/local/libexec/gpg-preset-passphrase --preset -P $GPG_PASSPHRASE $KEYGRIP
unset GPG_PASSPHRASE

echo "Starting the gpg-agent proxy"
#exec ega-socket-proxy '0.0.0.0:9010' /run/ega/S.gpg-agent.extra --certfile /etc/ega/ssl.cert --keyfile /etc/ega/ssl.key
exec ega-socket-proxy '0.0.0.0:9010' /root/.gnupg/S.gpg-agent.extra --certfile /etc/ega/ssl.cert --keyfile /etc/ega/ssl.key
