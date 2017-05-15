#!/usr/bin/env bash

VERSION=2.0
[ -n "$1" ] && VERSION=$1

pkill gpg-agent || true

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INGESTION_HOME=$HERE/..
source $HERE/details/gpg.credentials
HEXPWD=$(python -c "import binascii; print(binascii.hexlify(b'${PASSPHRASE}'))")



########### For GPG 2.0
if [ "$VERSION" == "2.0" ]; then
    # set -e
    # set -x
    export GNUPGHOME=$INGESTION_HOME/private/gpg

    [ -f $GNUPGHOME/gpg-agent.conf ] || cat > $GNUPGHOME/gpg-agent.conf <<EOF
allow-preset-passphrase
default-cache-ttl 2592000 # one month
max-cache-ttl 31536000    # one year
#
#debug-level guru
EOF

    [ -f $GNUPGHOME/gpg.conf ] || cat > $GNUPGHOME/gpg.conf <<EOF
# debug-all
# debug-level guru
#
# no-textmode
# batch
no-tty
keyring pubring.gpg
display-charset utf-8
utf8-strings
keyid-format long
#cipher-algo AES256
#s2k-digest-algo SHA256
#personal-cipher-preferences AES256,AES192,AES
#personal-digest-preferences SHA256,SHA1,MD5
EOF

    # GPG agent and homedir
    rm -f $GNUPGHOME/agent.env
    /usr/local/Cellar/gpg-agent/2.0.30_1/bin/gpg-agent --daemon --homedir $GNUPGHOME --write-env-file $GNUPGHOME/agent.env
    echo "export GPG_AGENT_INFO" >> $GNUPGHOME/agent.env
    echo "export GNUPGHOME=$GNUPGHOME" >> $GNUPGHOME/agent.env
    source $GNUPGHOME/agent.env


    KEYGRIP=$(gpg --homedir $GNUPGHOME --fingerprint --fingerprint ega@nbis.se |\
		  grep fingerprint | tail -1 | cut -d= -f2 | sed -e 's/ //g')
    /usr/local/Cellar/gpg-agent/2.0.30_1/libexec/gpg-preset-passphrase --preset -P $PASSPHRASE $KEYGRIP
    exit 0
fi

########### For GPG 2.1.20
if [ "$VERSION" == "2.1.20" ]; then
    set -e
    set -x
    export GNUPGHOME=$INGESTION_HOME/private/gpg.new
    GNUPG_LIBEXEC=/usr/local/Cellar/gnupg/$VERSION/libexec
    # GPG agent and homedir is started on demand now
    # So I just need to set the homedir
    gpg-agent --daemon --homedir $GNUPGHOME
    KEYGRIP=$(gpg --homedir $GNUPGHOME --fingerprint --fingerprint ega@nbis.se |\
		  grep fingerprint | tail -1 | cut -d= -f2 | sed -e 's/ //g')
    #${GNUPG_LIBEXEC}/gpg-preset-passphrase --homedir $GNUPGHOME -P $PASSPHRASE --preset $KEYGRIP 
    gpg-connect-agent --homedir $GNUPGHOME -q "PRESET_PASSPHRASE ${KEYGRIP} -1 ${HEXPWD}" /bye >/dev/null 2>&1 
    exit 0
fi

echo "Unknown version: $VERSION"
exit 1
