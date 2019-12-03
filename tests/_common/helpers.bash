#!/usr/bin/env bash

[ ${BASH_VERSINFO[0]} -lt 4 ] && echo 'Bash 4 (or higher) is required' 1>&2 && exit 1

HERE=$(dirname ${BASH_SOURCE[0]})
MAIN_REPO=${HERE}/../..

# Some variables for these tests
DOCKER_PATH=${MAIN_REPO}/deploy
EGA_PUBKEY=${DOCKER_PATH}/private/keys/ega.pub

# Default log file, in case the bats file does not overwrite its location.
#DEBUG_LOG=${HERE}/output.debug
DEBUG_LOG=${BATS_TEST_FILENAME}.debug

# Data directory
TESTDATA_DIR=$HERE
USERS_FILE=${DOCKER_PATH}/private/.users
TRACE_FILE=${DOCKER_PATH}/private/config/trace.yml

# If the CEGA_CONNECTION is not against hellgate (ie Central EGA)
# then it is against the fake one, which is deployed on the same network
# as LocalEGA components, and accessible from the localhost via a port mapping
CEGA_PASSWORD=$(cat ${TRACE_FILE} | shyaml get-value secrets.cega_mq_pass)
export CEGA_CONNECTION="amqps://lega:${CEGA_PASSWORD}@localhost:5670/lega"

# Create certfile/keyfile for testsuite
cp -f ${MAIN_REPO}/deploy/private/config/certs/tester.ca.{key,crt} ${HERE}/mq/.
cp -f ${MAIN_REPO}/deploy/private/config/certs/root.ca.crt ${HERE}/mq/.

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


function load_into_ssh_agent {
    local user=$1

    [[ -z "${SSH_AGENT_PID}" ]] && echo "The ssh-agent was not started" >&2 && return 2

    while IFS=: read -a info; do
	echo "Compare with ${info[0]} == ${user}" >&3
	if [[ "${info[0]}" == "${user}" ]]; then
	    expect &>/dev/null <<EOF
set timeout -1
spawn ssh-add ${info[1]}
expect "Enter passphrase for *"
send -- "${info[2]}\r"
expect eof
EOF
	    #break
	    return 0
	fi
    done < ${USERS_FILE}
    return 1
}

function _get_user_info {
    local pos=$1
    local user=$2

    while IFS=: read -a info; do
	if [[ "${info[0]}" == "${user}" ]]; then
	    echo -n "${info[$pos]}"
	    #break
	    return 0
	fi
    done < ${USERS_FILE}
    return 1
}


function get_user_seckey {
    _get_user_info 1 $1
}
function get_user_passphrase {
    _get_user_info 2 $1
}

