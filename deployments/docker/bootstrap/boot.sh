#!/usr/bin/env bash
set -e

HERE=$(dirname ${BASH_SOURCE[0]})
PRIVATE=${HERE}/../private
DOT_ENV=${HERE}/../.env
SETTINGS=${HERE}/settings

# Defaults
VERBOSE=no
FORCE=yes
OPENSSL=openssl
GPG=gpg2
GPG_CONF=gpgconf

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value> \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--gpg <value>     \tPath to the GnuPG executable [Default: ${GPG}]"
    echo -e "\t--gpgconf <value> \tPath to the GnuPG conf executable [Default: ${GPG_CONF}]"
    echo ""
    echo -e "\t--verbose, -v     \tShow verbose output"
    echo -e "\t--polite, -p      \tDo not force the re-creation of the subfolders. Ask instead"
    echo -e "\t--help, -h        \tOutputs this message and exits"
    echo -e "\t-- ...            \tAny other options appearing after the -- will be ignored"
    echo ""
}

# While there are arguments or '--' is reached
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage; exit 0;;
        --verbose|-v) VERBOSE=yes;;
        --polite|-p) FORCE=no;;
	--gpg) GPG=$2; shift;;
	--gpgconf) GPG_CONF=$2; shift;;
        --openssl) OPENSSL=$2; shift;;
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source ${HERE}/defs.sh

INSTANCES=$(ls ${SETTINGS} | xargs) # make it one line. ls -lx didn't work

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}/cega
backup ${DOT_ENV}

exec 2>${PRIVATE}/.err

cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=ega
COMPOSE_FILE=ega.yml
DATA=./private
EOF
# Do not use ${PRIVATE}: Wrong path if run in container

cat >> ${PRIVATE}/cega/env <<EOF
LEGA_INSTANCES=${INSTANCES// /,}
EOF

# Central EGA Users
source ${HERE}/cega_users.sh

# Generate the configuration for each instance
for INSTANCE in ${INSTANCES}; do source ${HERE}/instance.sh; done

# Central EGA Message Broker. Must be run after the instances
source ${HERE}/cega_mq.sh

task_complete "Bootstrap complete"
