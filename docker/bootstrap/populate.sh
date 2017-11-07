#!/usr/bin/env bash

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

# Defaults:
VERBOSE=yes
FORCE=no
PRIVATE=private
SOURCES=$HERE/../../src
ENTRYPOINTS=$HERE/../entrypoints

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--private_dir <path>         \tPath location of private data folder"
    echo -e "\t--sources <path>             \tPath Location of the src folder"
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
        --sources) SOURCES=$2; shift;;
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

case $SOURCES in
    /*)  ABS_SOURCES=$SOURCES;;
    ./*|../*) ABS_SOURCES=$PWD/$SOURCES;;
    *) ABS_SOURCES=$HERE/$SOURCES;;
esac

[[ -d $SOURCES ]] || { echomsg "Sources folder $ABS_SOURCES not found. Exiting" 1>&2; exit 1; }

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
CODE=${ABS_SOURCES}
ENTRYPOINTS=${ABS_ENTRYPOINTS}
#
CEGA_USERS=$ABS_PRIVATE/cega/users
CEGA_MQ_DEFS=$ABS_PRIVATE/cega/mq/defs.json
EOF

eval $(grep LEGA_INSTANCES $HERE/defaults/cega)

INSTANCES=(${LEGA_INSTANCES/,/ }) # make it an array

for INSTANCE in "${INSTANCES[@]}"; do
    cat >> $HERE/../.env <<EOF
#
CONF_${INSTANCE}=$ABS_PRIVATE/${INSTANCE}/ega.conf
KEYS_${INSTANCE}=$ABS_PRIVATE/${INSTANCE}/keys.conf
#
SSL_CERT_${INSTANCE}=$ABS_PRIVATE/${INSTANCE}/certs/ssl.cert
SSL_KEY_${INSTANCE}=$ABS_PRIVATE/${INSTANCE}/certs/ssl.key
RSA_SEC_${INSTANCE}=$ABS_PRIVATE/${INSTANCE}/rsa/ega.sec
RSA_PUB_${INSTANCE}=$ABS_PRIVATE/${INSTANCE}/rsa/ega.pub
GPG_HOME_${INSTANCE}=$ABS_PRIVATE/${INSTANCE}/gpg
EOF
done

cp -rf $ABS_PRIVATE/.env.d $HERE/../.env.d

# Updating .trace with the right path
if [[ -f $ABS_PRIVATE/.trace.cega ]]; then
    sed "s#<bootstrap>#$HERE#g" $ABS_PRIVATE/.trace.cega > $ABS_PRIVATE/.trace.cega.tmp
    mv -f $ABS_PRIVATE/.trace.cega.tmp $ABS_PRIVATE/.trace.cega
    # Note: The -i did not work. Dunno why.
fi

echomsg "docker-compose configuration files populated"
