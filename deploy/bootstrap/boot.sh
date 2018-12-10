#!/usr/bin/env bash
set -e

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

HERE=$(dirname ${BASH_SOURCE[0]})
PRIVATE=${HERE}/../private
DOT_ENV=${HERE}/../.env
EXTRAS=${HERE}/../../../extras

# Defaults
VERBOSE=no
FORCE=yes
OPENSSL=openssl
INBOX=openssh
KEYSERVER=lega


function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value> \tPath to the Openssl executable [Default: ${OPENSSL}]"
    echo -e "\t--inbox <value>   \tSelect inbox \"openssh\" or \"mina\" [Default: ${INBOX}]"
    echo -e "\t--keyserver <value>   \tSelect keyserver \"lega\" or \"ega\" [Default: ${KEYSERVER}]"
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
        --openssl) OPENSSL=$2; shift;;
        --inbox) INBOX=$2; shift;;
        --keyserver) KEYSERVER=$2; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping "

source ${HERE}/defs.sh

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

rm_politely ${PRIVATE}
mkdir -p ${PRIVATE}/{cega,lega}
exec 2>${PRIVATE}/.err
backup ${DOT_ENV}
cat > ${DOT_ENV} <<EOF
COMPOSE_PROJECT_NAME=lega
COMPOSE_FILE=private/cega.yml:private/lega.yml
EOF
# Don't use ${PRIVATE}, since it's running in a container: wrong path then.

source ${HERE}/settings.rc

# Central EGA Users and Eureka server
source ${HERE}/cega.sh

# Generate the configuration for each instance
echomsg "Generating private data for a LocalEGA instance"
source ${HERE}/lega.sh

task_complete "Bootstrap complete"
