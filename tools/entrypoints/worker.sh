#!/bin/bash

set -e

pip install -e /root/ega

pkill gpg-agent || true

HEXPWD=$(python -c "import binascii; print(binascii.hexlify(b'${PASSPHRASE}'))")

AGENT_ENV=/tmp/gpg-agent.env

# GPG agent and homedir
rm -f $AGENT_ENV
gpg-agent --daemon --homedir $GNUPGHOME --write-env-file $AGENT_ENV

KEYGRIP=$(gpg --homedir $GNUPGHOME --fingerprint --fingerprint ega@nbis.se |\
	      grep fingerprint | tail -1 | cut -d= -f2 | sed -e 's/ //g')

source $AGENT_ENV
/usr/libexec/gpg-preset-passphrase --preset -P $PASSPHRASE $KEYGRIP

sleep 6
exec ega-worker
