#!/bin/bash

set -e

pip install -e /root/ega

chmod 700 /root/.gnupg

pkill gpg-agent || true
#/usr/local/bin/gpgconf --kill gpg-agent || true
rm -rf $(gpgconf --list-dirs agent-extra-socket) || true

# Start the GPG Agent in /root/.gnupg
/usr/local/bin/gpg-agent --daemon

#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(/usr/local/bin/gpg -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
/usr/local/libexec/gpg-preset-passphrase --preset -P $GPG_PASSPHRASE $KEYGRIP
unset GPG_PASSPHRASE

echo "Starting the gpg-agent proxy"
exec ega-socket-proxy '0.0.0.0:9010' /root/.gnupg/S.gpg-agent.extra \
		     --certfile /etc/ega/ega.cert --keyfile /etc/ega/ega.key
		     #--log /root/ega/lega/conf/loggers/debug.yaml
