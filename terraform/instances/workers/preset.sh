#!/bin/bash

set -e

##############
#while gpg-connect-agent /bye; do sleep 2; done
KEYGRIP=$(/usr/local/bin/gpg -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
if [ ! -z "$KEYGRIP" ]; then 
    echo 'Unlocking the GPG key'
    # This will use the standard socket. The proxy forwards to the extra socket.
    /usr/local/libexec/gpg-preset-passphrase --preset -P "$(cat /tmp/gpg_passphrase)" $KEYGRIP
    # && rm -f /tmp/gpg_passphrase
else
    echo 'Skipping the GPG key preseting'
fi

