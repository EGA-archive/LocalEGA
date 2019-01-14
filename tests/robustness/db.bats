#!/usr/bin/env bats

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Defining the TMP dir
    TESTFILES=${BATS_TEST_FILENAME}.d
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
    rm -rf ${TESTFILES}
}

# Utility to ingest successfully a file
function lega_ingest {
    local TESTFILE=$1
    local size=$2
    local queue=$3

    # Create a random file Crypt4GH file of 1 MB
    legarun c4gh_generate 1 /dev/urandom ${TESTFILES}/${TESTFILE}
    [ "$status" -eq 0 ]

    # Upload it
    UPLOAD_CMD="put ${TESTFILES}/${TESTFILE}.c4ga /${TESTFILE}.c4ga"
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< ${UPLOAD_CMD}
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
    # Waiting 20 seconds.
    retry_until 0 10 2 ${MQ_GET} $queue "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
}

# Ingestion after db restart
# --------------------------
# Ingest a file, stop db, start db, ingest another file

@test "Ingestion after db restart" {
    skip "Used after the update for DB connection retries"

    lega_ingest $(uuidgen) 1 v1.files.completed
    legarun docker stop db
    legarun docker start db
    legarun sleep 15
    lega_ingest $(uuidgen) 1 v1.files.completed

}

# DB restart in the middle of ingestion
# -------------------------------------

@test "DB restart in the middle of ingestion" {
    skip "Used after the update for DB connection retries"

    TESTFILE=$(uuidgen)

    # Stop the verify component, so only ingest works
    legarun docker stop verify

    # Create a random file Crypt4GH file of 1 MB
    legarun c4gh_generate 1 /dev/urandom ${TESTFILES}/${TESTFILE}
    [ "$status" -eq 0 ]

    # Upload it
    UPLOAD_CMD="put ${TESTFILES}/${TESTFILE}.c4ga /${TESTFILE}.c4ga"
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< ${UPLOAD_CMD}
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${TESTFILE}.c4ga\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID} files "$MESSAGE"
    [ "$status" -eq 0 ]


    # Restart database
    legarun docker stop db
    legarun docker start db
    legarun sleep 15

    # Restart verify
    legarun docker restart verify
    legarun sleep 15

    # Check that a message with the above correlation id arrived in the expected queue
    retry_until 0 10 2 ${MQ_GET} v1.files.completed "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
}
