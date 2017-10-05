#!/usr/bin/env bash

SCRIPT=$(dirname ${BASH_SOURCE[0]})
HERE=$PWD/${SCRIPT#./}

# Defaults:
VERBOSE=yes
FORCE=no
PRIVATE=private

function usage {
    echo "Usage: $0 [options]"
    echo -e "\nOptions are:"
    echo -e "\t--private_dir <name>         \tName of the main folder for private data"
    echo -e "\t--force, -f                  \tForce the re-creation of the subfolders"
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
        --private_dir) PRIVATE=$2; shift;;
        --) shift; break;;
        *) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

case $PRIVATE in
    /*)  ABS_PRIVATE=$PRIVATE;;
    ./*|../*) ABS_PRIVATE=$PWD/$PRIVATE;;
    *) ABS_PRIVATE=$HERE/$PRIVATE;;
esac

[[ -d $ABS_PRIVATE ]] || { echo "Private data folder $ABS_PRIVATE not found. Exiting"; exit 1; }

echo "Copying the docker-compose environment"
DEST=$HERE/..

function backup {
    local target=$1
    if [[ -e $target ]]; then
	mv -f $target $target.$(date +"%Y-%m-%d_%H:%M:%S")
    fi
}

[[ $FORCE == 'yes' ]] || backup $HERE/../.env
[[ $FORCE == 'yes' ]] || backup $HERE/../.env.d

mv -f $ABS_PRIVATE/.env $DEST/.env
mv -f $ABS_PRIVATE/.env.d $DEST/.env.d

