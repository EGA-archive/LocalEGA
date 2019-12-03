#!/usr/bin/env bats

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Defining the TMP dir
    TESTFILES=${BATS_TEST_FILENAME}.d
    mkdir -p "$TESTFILES"

    # Start an SSH-agent for this env
    eval $(ssh-agent) &>/dev/null
    # That adds SSH_AUTH_SOCK and SSH_AUTH_PID to this env

    [[ -z "${SSH_AGENT_PID}" ]] && echo "Could not start the local ssh-agent" 2>/dev/null && exit 2

    # Test user
    TESTUSER=dummy
    load_into_ssh_agent ${TESTUSER}
    [[ $? != 0 ]] && echo "Error loading the test user into the local ssh-agent" >&2 && exit 3

    TESTUSER_SECKEY=$(get_user_seckey ${TESTUSER})
    TESTUSER_PASSPHRASE=$(get_user_passphrase ${TESTUSER})


    # Find inbox port mapping. Usually 2222:9000
    INBOX_PORT="2222"
    # legarun docker port inbox 9000
    # [ "$status" -eq 0 ]
    # INBOX_PORT=${output##*:}
    LEGA_SFTP="sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INBOX_PORT}"
}

function teardown() {
    rm -rf ${TESTFILES}

    # Kill an SSH-agent for this env
    [[ -n "${SSH_AGENT_PID}" ]] && kill -TERM "${SSH_AGENT_PID}"
}

# Utility to ingest successfully a file
function lega_ingest {
    local TESTFILE=$1
    local size=$2 # in MB
    local queue=$3
    local inputsource=${4:-/dev/urandom}

    [ -n "${TESTUSER}" ]
    [ -n "${TESTUSER_SECKEY}" ]
    [ -n "${TESTUSER_PASSPHRASE}" ]

    # Create a random file of 1 MB
    legarun dd if=/dev/urandom of=${TESTFILES}/${TESTFILE} count=1 bs=1048576
    [ "$status" -eq 0 ]

    export C4GH_PASSPHRASE=${TESTUSER_PASSPHRASE}
    crypt4gh encrypt --sk ${TESTUSER_SECKEY} --recipient_pk ${EGA_PUBKEY} < ${TESTFILES}/${TESTFILE} > ${TESTFILES}/${TESTFILE}.c4ga
    unset C4GH_PASSPHRASE

    # Upload it
    UPLOAD_CMD="put ${TESTFILES}/${TESTFILE}.c4ga /${TESTFILE}.c4ga"
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< ${UPLOAD_CMD}
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${TESTFILE}.c4ga\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID} files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Check that a message with the above correlation id arrived in the expected queue
    # Waiting 200 seconds.
    retry_until 0 20 10 ${MQ_GET} $queue "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
}

# Ingesting a 10MB file
# ----------------------
# A message should be found in the completed queue

@test "Ingest properly a 10MB file" {
    lega_ingest $(uuidgen) 10 v1.files.completed
}

# Ingesting a "big" file
# ----------------------
# A message should be found in the completed queue
#
# Note: We have tested with a 10 GB file by hand,
# and we are here 'only' ingesting a 1 GB file (for speed)
# Moreover, we are depleting the random pool,
# so we're using the /dev/zero for that particular test

@test "Ingest properly a 1GB file" {
    lega_ingest $(uuidgen) 1000 v1.files.completed /dev/zero
}

# Upload 2 files encrypted with same session key
# ----------------------------------------------
# This is done by uploading the same file twice.
#
# The first upload should end up in the completed queue
# while the second one should be in the error queue

@test "Do not ingest the same file twice" {
    skip
    # We skip it for the moment since the codebase is old
    # and does not support this functionality

    TESTFILE=$(uuidgen)
    
    # First time
    lega_ingest ${TESTFILE} 1 v1.files.completed

    # Second time
    UPLOAD_CMD="put ${TESTFILES}/${TESTFILE}.c4ga /${TESTFILE}.c4ga.2"
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< ${UPLOAD_CMD}
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${TESTFILE}.c4ga.2"
    [ "$status" -eq 0 ]
    CORRELATION_ID2=$output
    [ "$CORRELATION_ID" != "$CORRELATION_ID2" ]

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE2="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${TESTFILE}.c4ga.2\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID2} files "$MESSAGE2"
    [ "$status" -eq 0 ]

    # Check that a message with the above correlation id arrived in the error queue
    retry_until 0 10 10 ${MQ_GET} v1.files.error "${TESTUSER}" "/${TESTFILE}.c4ga.2"
    [ "$status" -eq 0 ]
}

# Ingesting a file not in Crypt4GH format
# ---------------------------------------
#
# We encrypt a testfile with AES and ingest it.
# A message should be found in the error queue

@test "Do not ingest a file not in Crypt4GH format" {
    TESTFILE=$(uuidgen)

    # Create a random file of 1 MB
    legarun dd if=/dev/urandom of=${TESTFILES}/${TESTFILE} count=1 bs=1048576
    [ "$status" -eq 0 ]

    # Encrypt it with AES
    legarun openssl enc -aes-256-cbc -e -in ${TESTFILES}/${TESTFILE} -out ${TESTFILES}/${TESTFILE}.c4ga -k 'secretpassword'
    [ "$status" -eq 0 ]

    # Upload it
    UPLOAD_CMD="put ${TESTFILES}/${TESTFILE}.c4ga /${TESTFILE}.c4ga"
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< ${UPLOAD_CMD}
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${TESTFILE}.c4ga\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID} files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Check that a message with the above correlation id arrived in the completed queue
    retry_until 0 10 10 ${MQ_GET} v1.files.error "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
}

# Ingesting a file from a subdirectory
# ------------------------------------
# A message should be found in the completed queue.

@test "Ingest a file from a subdirectory" {
    mkdir -p ${TESTFILES}/dir1/dir2/dir3
    # SFTP requires that the remote directory be existing.
    # However the sftp commands are very limited (mkdir -p dir1/dir2/dir3 in invalid, and mkdir takes one dir at a time)
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< $"mkdir dir1"
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< $"mkdir dir1/dir2"
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< $"mkdir dir1/dir2/dir3"
    lega_ingest dir1/dir2/dir3/$(uuidgen) 1 v1.files.completed
}


# Ingesting a file with the wrong LocalEGA PGP key
# ------------------------------------------------
#
# Create a temporary new PGP key, as if it was another LocalEGA
# The keyserver does not have that key, so ingestion should raise an error
# Note: the EGA keyserver returns a 200 with an empty payload,
# so the verify is adjusted to correct that bug.
#
# A message should be found in the error queue, because it is a user error

@test "Do not ingest file destined for another LocalEGA" {

    # Create another key, and make the utility use it
    FAKE_PASSPHRASE=fake
    EGA_SECKEY=${TESTFILES}/fake.sec
    EGA_PUBKEY=${TESTFILES}/fake.pub
    cat > ${TESTFILES}/fake_keygen.sh <<EOF
set timeout -1
spawn crypt4gh-keygen --sk ${EGA_SECKEY} --pk ${EGA_PUBKEY} -f
expect "Passphrase for *"
send -- "${FAKE_PASSPHRASE}\r"
expect eof
EOF
    expect -f ${TESTFILES}/fake_keygen.sh &>/dev/null
    rm -f ${TESTFILES}/fake_keygen.sh
    
    # This will use EGA_PUBKEY
    lega_ingest $(uuidgen) 1 v1.files.error
}

###### Notes
# Tests used to check the messages using the Correlation ID.
# However, the codebase is old and the correlation ID update is not part of it
# So, instead, we use the filepath and the username to filter out the messages.
# When the update is in place, the line
#     retry_until 0 100 1 ${MQ_GET} v1.files.error "${TESTUSER}" "${TESTFILE}.c4ga"
# will be updated with
#     retry_until 0 10 1 ${MQ_FIND} <queue> ${CORRELATION_ID}
#
# The name of the testfile can be ${BATS_TEST_NAME}, however, multiple runs of the testsuite
# would produce multiple message in the queues and the MQ_GET/MQ_FIND would get confused.
# We therefore use a uuid name, which can later be updated back to ${BATS_TEST_NAME}
