#!/usr/bin/env bash

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

HERE=$(dirname ${BASH_SOURCE[0]})
MAIN_REPO=${HERE}/../..

# Some variables for these tests
DOCKER_PATH=${MAIN_REPO}/deploy
EGA_PUB_KEY=${DOCKER_PATH}/private/pgp/ega.pub

# Default log file, in case the bats file does not overwrite its location.
#DEBUG_LOG=${HERE}/output.debug
DEBUG_LOG=${BATS_TEST_FILENAME}.debug

# Data directory
TESTDATA_DIR=$HERE

# If the CEGA_CONNECTION is not against hellgate (ie Central EGA)
# then it is against the fake one, which is deployed on the same network
# as LocalEGA components, and accessible from the localhost via a port mapping
if [[ "${CEGA_CONNECTION}" != *hellgate* ]]; then
    export CEGA_CONNECTION="amqps://legatest:legatest@localhost:5670/lega"
fi

# Create certfile/keyfile for testsuite
yes | make --silent -C ${MAIN_REPO}/deploy/bootstrap/certs testsuite &>/dev/null
cp -f ${MAIN_REPO}/deploy/bootstrap/certs/data/testsuite.{cert,sec}.pem ${HERE}/mq/.
cp -f ${MAIN_REPO}/deploy/bootstrap/certs/data/CA.cert.pem ${HERE}/mq/.

# Utilities to scan the Message Queues
MQ_CONSUME="python ${HERE}/mq/consume.py --connection ${CEGA_CONNECTION}"
MQ_FIND="python ${HERE}/mq/find.py --connection ${CEGA_CONNECTION}"
MQ_GET="python ${HERE}/mq/get.py --connection ${CEGA_CONNECTION}"
MQ_PUBLISH="python ${HERE}/mq/publish.py --connection ${CEGA_CONNECTION}"

# Convenience function to capture _all_ outputs
function legarun {
    echo -e "+++ $@" >> $DEBUG_LOG
    run "$@"
    echo -e "$output" >> $DEBUG_LOG
    echo -e "--- Status: $status" >> $DEBUG_LOG
}

# For OSX and Linux
function get_shasum {
    if command -v shasum &>/dev/null; then
        shasum -a 256 $1 | cut -d' ' -f1
    else
        sha256sum $1 | cut -d' ' -f1
    fi
}

# Check status $1 for a command, $2 times. Wait $3 seconds between retries.
function retry_until {
	local expected=$1
	local attempts=$2
	local delay=$3
	shift
	shift
	shift
	local i

	for ((i=0; i < attempts; i++)); do
	    echo -e "*** Attempt: ${i}/${attempts}" >> $DEBUG_LOG
	    legarun "$@"
	    if [[ "$status" -eq "$expected" ]] ; then
		return 0
	    fi
	    sleep $delay
	done

	echo -e "Command \"$@\" failed $attempts times. Output: $output" >> $DEBUG_LOG
	false
}
