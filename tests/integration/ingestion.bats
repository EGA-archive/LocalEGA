#!/usr/bin/env bats

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Changing the LOG file location
    DEBUG_LOG=$BATS_TEST_DIRNAME/output.debug

    # Defining the TMP dir
    TESTFILES=$BATS_TEST_DIRNAME/tmpfiles
    mkdir -p "$TESTFILES"

    # Test user
    TESTUSER=dummy

    # Utilities to scan the Message Queues
    MQ_FIND="python ${MAIN_REPO}/extras/rabbitmq/find.py --connection ${CEGA_CONNECTION}"
    MQ_GET="python ${MAIN_REPO}/extras/rabbitmq/get.py --connection ${CEGA_CONNECTION}"
    MQ_PUBLISH="python ${MAIN_REPO}/extras/rabbitmq/publish.py --connection ${CEGA_CONNECTION}"

    # Find inbox port mapping. Usually 2222:9000
    legarun docker port inbox 9000
    [ "$status" -eq 0 ]
    INBOX_PORT=${output##*:}
    LEGA_SFTP="sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P $INBOX_PORT"
}

function teardown() {
    rm -rf "$TESTFILES"
}

# Utility to ingest successfully a file
function lega_ingest {
    local size=${1:-10}
    # Note: BATS_TEST_NAME is set when the function is called

    # Create a random file of {size} MB
    legarun dd if=/dev/urandom of=${TESTFILES}/${BATS_TEST_NAME} count=$size bs=1048576
    [ "$status" -eq 0 ]

    # Encrypt it in the Crypt4GH format
    ENC_FILE=${TESTFILES}/${BATS_TEST_NAME}.c4ga
    legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${BATS_TEST_NAME} -o ${ENC_FILE}
    [ "$status" -eq 0 ]

    # Upload it
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< $"put ${ENC_FILE} /${BATS_TEST_NAME}.c4ga"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 2 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${BATS_TEST_NAME}.c4ga"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${BATS_TEST_NAME}.c4ga\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID} files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Check that a message with the above correlation id arrived in the completed queue
    retry_until 0 10 1 ${MQ_FIND} v1.files.completed ${CORRELATION_ID}
    [ "$status" -eq 0 ]
}

# Ingesting a 10MB file
# ----------------------
# A message should be found in the completed queue

@test "Ingesting properly a 10MB file" {
    lega_ingest 10
}

# Ingesting a "big" file
# ----------------------
# A message should be found in the completed queue
# Change the 100MB to a bigger number if necessary

@test "Ingesting properly a 100MB file" {
    lega_ingest 100
}

# Upload 2 files encrypted with same session key
# ----------------------------------------------
# This is done by uploading the same file twice.
#
# The first upload should end up in the completed queue
# while the second one should be in the error queue

@test "Ingesting the same file twice" {
    skip
    # We skip it for the moment since the codebase is old
    # and does not support this functionality
    
    # First time
    lega_ingest 1

    # Second time
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< $"put ${ENC_FILE} /${BATS_TEST_NAME}.c4ga.2"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 2 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${BATS_TEST_NAME}.c4ga.2"
    [ "$status" -eq 0 ]
    CORRELATION_ID2=$output
    [ "$CORRELATION_ID" != "$CORRELATION_ID2" ]

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE2="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${BATS_TEST_NAME}.c4ga.2\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID2} files "$MESSAGE2"
    [ "$status" -eq 0 ]

    # Check that a message with the above correlation id arrived in the completed queue
    retry_until 0 10 1 ${MQ_FIND} v1.files.error ${CORRELATION_ID2}
    [ "$status" -eq 0 ]
}
