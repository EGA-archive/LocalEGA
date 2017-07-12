#!/bin/bash

set -e

# cat /root/.ssh/ega.pub >> /root/.ssh/authorized_keys && \
# chmod 600 /root/.ssh/authorized_keys

pip install -e /root/ega

# cat > /tmp/ega <<EOF
# %echo Generating a basic OpenPGP key
# Key-Type: RSA
# Key-Length: 4096
# Name-Real: EGA Sweden
# Name-Comment: @NBIS
# Name-Email: ega@nbis.se
# Expire-Date: 0
# Passphrase: ${GPG_PASSPHRASE}
# # Do a commit here, so that we can later print "done" :-)
# %commit
# %echo done
# EOF
# gpg2 --batch --generate-key /tmp/ega
# rm -f /tmp/ega

chmod 700 /root/.gnupg

pkill gpg-agent || true
#/usr/local/bin/gpgconf --kill gpg-agent || true
rm -rf $(gpgconf --list-dirs agent-extra-socket) || true

# Start the GPG Agent in /root/.gnupg
/usr/local/bin/gpg-agent --daemon

KEYGRIP=$(gpg2 -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
/usr/local/libexec/gpg-preset-passphrase --preset -P $GPG_PASSPHRASE $KEYGRIP
unset GPG_PASSPHRASE

#while gpg-connect-agent /bye; do sleep 2; done
# Absolute path to version 7.5
#exec /usr/local/sbin/sshd -4 -D -e

exec ega-gpg-proxy
