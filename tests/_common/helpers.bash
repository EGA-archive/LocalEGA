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

# If the CEGA_CONNECTION is not against hellgate (ie Central EGA)
# then it is against the fake one, which is deployed on the same network
# as LocalEGA components, and accessible from the localhost via a port mapping
export CEGA_CONNECTION="amqps://legatest:legatest@localhost:5670/lega"

# Create certfile/keyfile for testsuite
#yes | make --silent -C ${MAIN_REPO}/deploy/bootstrap/certs testsuite OPENSSL=${OPENSSL:-openssl} &>/dev/null
cp -f ${MAIN_REPO}/deploy/bootstrap/certs/data/testsuite.{cert,sec}.pem ${HERE}/mq/.
cp -f ${MAIN_REPO}/deploy/bootstrap/certs/data/CA.cert.pem ${HERE}/mq/.

# Utilities to scan the Message Queues
MQ_CONSUME="python ${HERE}/mq/consume.py --connection ${CEGA_CONNECTION}"
MQ_FIND="python ${HERE}/mq/find.py --connection ${CEGA_CONNECTION}"
MQ_GET_INBOX="python ${HERE}/mq/get.py --connection ${CEGA_CONNECTION} v1.files.inbox"
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
	# echo "Compare with ${info[0]} == ${user}" >&3
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



# Utility to ingest successfully a file

function lega_generate_file {
    local TESTFILE=$1
    local TESTFILE_ENCRYPTED=$2
    local size=$3 # in MB
    local inputsource=${4:-/dev/urandom}

    [ -n "${TESTUSER_SECKEY}" ]
    [ -n "${TESTUSER_PASSPHRASE}" ]

    # Generate a random file
    export C4GH_PASSPHRASE=${TESTUSER_PASSPHRASE}
    dd if=$inputsource bs=1048576 count=$size 2>/dev/null | \
	crypt4gh encrypt --sk ${TESTUSER_SECKEY} --recipient_pk ${EGA_PUBKEY} 2>/dev/null > ${TESTFILE_ENCRYPTED}
    unset C4GH_PASSPHRASE
}

function lega_upload {
    local TESTFILE_ENCRYPTED=$1
    local TESTFILE_UPLOADED=$2

    [ -n "${TESTUSER}" ]
    [ -n "${INBOX_PORT}" ]
    
    LEGA_SFTP="sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INBOX_PORT}"
    UPLOAD_CMD="put ${TESTFILE_ENCRYPTED} ${TESTFILE_UPLOADED}" # start with / or not ?
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< ${UPLOAD_CMD}
    [ "$status" -eq 0 ]
}


function lega_trigger_ingestion {
    local user=$1
    local upload_path=$2
    local queue=$3
    local attempts=$4
    local delay=$5

    [ -n "${user}" ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 $attempts $delay ${MQ_GET_INBOX} "${user}" "${upload_path}"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${user}\", \"filepath\": \"${upload_path}\"}"
    legarun ${MQ_PUBLISH} --correlation_id "${CORRELATION_ID}" files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Check that a message with the above correlation id arrived in the expected queue
    # Waiting attemps * delay seconds.
    retry_until 0 $attempts $delay ${MQ_FIND} $queue "${CORRELATION_ID}"
    [ "$status" -eq 0 ]

    # The message should contain the same info as the trigger message
    [[ "$output" =~ "user: dummy" ]]
    [[ "$output" =~ "filepath: ${upload_path}" ]]
}


function lega_ingest {
    local TESTFILE=$1
    local size=$2 # in MB
    local queue=$3
    local inputsource=${4:-/dev/urandom}

    TESTFILE_ENCRYPTED="${TESTFILES}/${TESTFILE}.c4gh"
    TESTFILE_UPLOADED="/${TESTFILE}.c4gh"

    # Generate a random file
    lega_generate_file ${TESTFILE} ${TESTFILE_ENCRYPTED} $size $inputsource

    # Upload it
    lega_upload "${TESTFILE_ENCRYPTED}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]

    lega_trigger_ingestion "${TESTUSER}" "${TESTFILE_UPLOADED}" $queue 30 10
}

