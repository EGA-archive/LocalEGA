#!/bin/bash

set -e

##############
# Public + Private parts
mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
mkdir -p ~/.rsa && chmod 700 ~/.rsa
mkdir -p ~/certs && chmod 700 ~/certs
mkdir -p ~/.gnupg/private-keys-v1.d && chmod 700 ~/.gnupg/private-keys-v1.d

unzip /tmp/gpg.zip -d ~/.gnupg
unzip /tmp/gpg_private.zip -d ~/.gnupg/private-keys-v1.d
unzip /tmp/rsa.zip -d ~/.rsa
unzip /tmp/certs.zip -d ~/certs

rm /tmp/gpg.zip
rm /tmp/gpg_private.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

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
sudo systemctl start ega-socket-proxy
sudo systemctl enable ega-socket-proxy

echo "Master GPG-agent ready"
