#!/usr/bin/env bash

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

# Defaults:
VERBOSE=yes
FORCE=no
PRIVATE=private
ENTRYPOINTS=$HERE/../entrypoints

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--private_dir <path>         \tPath location of private data folder"
    echo -e "\t--entrypoints <path>         \tPath Location of the entrypoints folder"
    echo -e "\t--force, -f                  \tDon't backup .env and .env.d if they exist"
    echo -e "\t--quiet, -q                  \tRemoves the verbose output (and uses -f)"
    echo -e "\t--help, -h                   \tOutputs this message and exits"
    echo -e "\t-- ...                       \tAny other options appearing after the -- will be ignored"
    echo ""
}

# While there are arguments or '--' is reached
while [[ $# -gt 0 ]]; do
    case "$1" in
        --quiet|-q) VERBOSE=no;;
        --help|-h) usage; exit 0;;
        --force|-f) FORCE=yes;;
        --entrypoints) ENTRYPOINTS=$2; shift;;
        --private_dir) PRIVATE=$2; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

function echomsg {
    [[ $VERBOSE == 'yes' ]] && echo $@
}

case $PRIVATE in
    /*)  ABS_PRIVATE=$PRIVATE;;
    ./*|../*) ABS_PRIVATE=$PWD/$PRIVATE;;
    *) ABS_PRIVATE=$HERE/$PRIVATE;;
esac

[[ -d $ABS_PRIVATE ]] || { echomsg "Private data folder $ABS_PRIVATE not found. Exiting" 1>&2; exit 1; }

case $ENTRYPOINTS in
    /*)  ABS_ENTRYPOINTS=$ENTRYPOINTS;;
    ./*|../*) ABS_ENTRYPOINTS=$PWD/$ENTRYPOINTS;;
    *) ABS_ENTRYPOINTS=$HERE/$ENTRYPOINTS;;
esac

[[ -d $ABS_ENTRYPOINTS ]] || { echomsg "Entrypoints folder $ABS_ENTRYPOINTS not found. Exiting" 1>&2; exit 1; }

function backup {
    local target=$1
    if [[ -e $target ]]; then
	echomsg "Backing up $target"
	mv -f $target $target.$(date +"%Y-%m-%d_%H:%M:%S")
    fi
}

[[ $FORCE == 'yes' ]] || {
    backup $HERE/../.env
    backup $HERE/../.env.d
}

# Populate env-settings for docker compose
cat > $HERE/../.env <<EOF
COMPOSE_PROJECT_NAME=ega
COMPOSE_FILE=ega.yml
ENTRYPOINTS=${ABS_ENTRYPOINTS}
CODE=${HERE}/../../src
CONF=$ABS_PRIVATE/ega.conf
KEYS=$ABS_PRIVATE/keys.conf
SSL_CERT=$ABS_PRIVATE/certs/ssl.cert
SSL_KEY=$ABS_PRIVATE/certs/ssl.key
RSA_SEC=$ABS_PRIVATE/rsa/ega.sec
RSA_PUB=$ABS_PRIVATE/rsa/ega.pub
GPG_HOME=$ABS_PRIVATE/gpg
CEGA_USERS=$ABS_PRIVATE/cega/users
CEGA_MQ_DEFS=$ABS_PRIVATE/cega/mq/defs.json
EOF

cp -rf $ABS_PRIVATE/.env.d $HERE/../.env.d

echomsg "docker-compose configuration files populated"
