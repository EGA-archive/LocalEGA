#!/bin/bash

set -e

chmod 700 ~/.gnupg
##############
# Public part
unzip /tmp/gpg_public.zip -d ~/.gnupg && \
rm /tmp/gpg_public.zip

mkdir -p -m 0700 ~/.rsa && \
unzip /tmp/rsa_public.zip -d ~/.rsa && \
rm /tmp/rsa_public.zip

mkdir -p -m 0700 ~/certs && \
unzip /tmp/certs_public.zip -d ~/certs && \
rm /tmp/certs_public.zip

##############
# Private part
mkdir -p -m 0700 ~/.gnupg/private-keys-v1.d && \
unzip /tmp/gpg_private.zip -d ~/.gnupg/private-keys-v1.d && \
rm /tmp/gpg_private.zip

mkdir -p -m 0700 ~/.rsa && \
unzip /tmp/rsa_private.zip -d ~/.rsa && \
rm /tmp/rsa_private.zip

mkdir -p -m 0700 ~/certs && \
unzip /tmp/certs_private.zip -d ~/certs && \
rm /tmp/certs_private.zip

##############
git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

##############
cat > ~/.gnupg/gpg-agent.conf <<EOF
#log-file gpg-agent.log
allow-preset-passphrase
default-cache-ttl 2592000 # one month
max-cache-ttl 31536000    # one year
pinentry-program /usr/local/bin/pinentry-curses
allow-loopback-pinentry
enable-ssh-support
extra-socket /home/ega/.gnupg/S.gpg-agent.extra
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF

echo "(Re-)starting the gpg-agent"
pkill gpg-agent || true
rm -rf $(gpgconf --list-dirs agent-extra-socket) || true

# Start the GPG Agent in ~/.gnupg
/usr/local/bin/gpg-agent --daemon

##############
#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(/usr/local/bin/gpg2 -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
if [ ! -z "$KEYGRIP" ]; then 
    echo 'Unlocking the GPG key'
    /usr/local/libexec/gpg-preset-passphrase --preset -P "$(cat /tmp/gpg_passphrase)" $KEYGRIP && \
	rm -f /tmp/gpg_passphrase
else
    echo 'Skipping the GPG key preseting'
fi

##############
echo "Starting the gpg-agent proxy"
ega-socket-proxy '0.0.0.0:9010' ~/.gnupg/S.gpg-agent.extra \
		 --certfile ~/certs/selfsigned.cert --keyfile ~/certs/selfsigned.key &

echo "Master GPG-agent ready"
