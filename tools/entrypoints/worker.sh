#!/bin/bash

set -e

pip install -e /root/ega

pkill gpg-agent || true

HEXPWD=$(python -c "import binascii; print(binascii.hexlify(b'${PASSPHRASE}'))")

TMP_GPG=/tmp/gnupg/

# GPG agent and homedir
rm -f $TMP_GPG/agent.env
gpg-agent --daemon --homedir $GNUPGHOME --write-env-file $TMP_GPG/agent.env
echo "export GPG_AGENT_INFO" >> $TMP_GPG/agent.env
echo "export GNUPGHOME=$GNUPGHOME" >> $TMP_GPG/agent.env
source $TMP_GPG/agent.env

KEYGRIP=$(gpg --homedir $GNUPGHOME --fingerprint --fingerprint ega@nbis.se |\
	      grep fingerprint | tail -1 | cut -d= -f2 | sed -e 's/ //g')
gpg-preset-passphrase --preset -P $PASSPHRASE $KEYGRIP

sleep 6
exec ega-worker
