#!/bin/bash

set -e

# cat > /tmp/ega <<EOF
# %echo Generating a basic OpenPGP key
# Key-Type: RSA
# Key-Length: 4096
# Name-Real: EGA Sweden
# Name-Comment: @NBIS
# Name-Email: ega@nbis.se
# Expire-Date: 0
# Passphrase: ${PASSPHRASE}
# # Do a commit here, so that we can later print "done" :-)
# %commit
# %echo done
# EOF
# gpg2 --batch --generate-key /tmp/ega
# rm -f /tmp/ega

pkill gpg-agent
# Start the GPG Agent in /root/.gnupg
/usr/local/bin/gpg-agent --daemon

KEYGRIP=$(gpg2 --fingerprint --fingerprint ega@nbis.se | grep fingerprint | tail -1 | cut -d= -f2 | sed -e 's/ //g')

/usr/local/libexec/gpg-preset-passphrase --preset -P $PASSPHRASE $KEYGRIP

unset PASSPHRASE

while true; do echo "Busy"; sleep 5; done
