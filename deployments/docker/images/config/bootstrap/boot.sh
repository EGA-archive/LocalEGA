#!/usr/bin/env bash
set -e

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

INSTANCE=fin
HERE=$(dirname ${BASH_SOURCE[0]})
PRIVATE=${HERE}/../config
SETTINGS=${HERE}/${INSTANCE}
EXTRAS=${HERE}/../../../extras

# Defaults
VERBOSE=no
FORCE=no
OPENSSL=openssl

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--openssl <value> \tPath to the Openssl executable [Default: ${OPENSSL}]"
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
	--) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;    esac
    shift
done

[[ $VERBOSE == 'no' ]] && echo -en "Bootstrapping LEGA "

source ${HERE}/defs.sh

# NOT REQUIRED
# INSTANCES=$(ls ${SETTINGS} | xargs) # make it one line. ls -lx didn't work

mkdir -p ${PRIVATE}
# exec 2>${PRIVATE}/.err

# NOT REQUIRED
# Generate the configuration for each instance
# for INSTANCE in ${INSTANCES}
# do
echomsg "Generating private data for ${INSTANCE} [Default in ${SETTINGS}]"
source ${HERE}/instance.sh
# done

task_complete "Bootstrap complete"
