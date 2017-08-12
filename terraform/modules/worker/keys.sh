#!/bin/bash

set -e

unzip /tmp/gpg.zip -d /root/.gnupg && \
rm /tmp/gpg.zip

mkdir -p -m 0700 /root/.rsa && \
unzip /tmp/rsa.zip -d /root/.rsa && \
rm /tmp/rsa.zip

mkdir -p -m 0700 /etc/ega && \
unzip /tmp/certs.zip -d /etc/ega && \
rm /tmp/certs.zip

git clone https://github.com/NBISweden/LocalEGA.git ~/ega
pip3.6 install -e ~/ega/src

chmod 700 /root/.gnupg

cat > /root/.gnupg/gpg-agent.conf <<EOF
#log-file gpg-agent.log
allow-preset-passphrase
default-cache-ttl 2592000 # one month
max-cache-ttl 31536000    # one year
pinentry-program /usr/local/bin/pinentry-curses
allow-loopback-pinentry
enable-ssh-support
extra-socket /root/.gnupg/S.gpg-agent.extra
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF

pkill gpg-agent || true
#/usr/local/bin/gpgconf --kill gpg-agent || true
rm -rf $(gpgconf --list-dirs agent-extra-socket) || true

# Start the GPG Agent in /root/.gnupg
/usr/local/bin/gpg-agent --daemon

#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(/usr/local/bin/gpg2 -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
if [ ! -z "$KEYGRIP" ]; then 
    /usr/local/libexec/gpg-preset-passphrase --preset -P "$(cat /tmp/gpg_passphrase)" $KEYGRIP && \
	rm -f /tmp/gpg_passphrase
else
    echo 'Skipping the GPG key preseting'
fi

echo "Starting the gpg-agent proxy"
ega-socket-proxy '0.0.0.0:9010' /root/.gnupg/S.gpg-agent.extra \
		 --certfile /etc/ega/selfsigned.cert --keyfile /etc/ega/selfsigned.key &
