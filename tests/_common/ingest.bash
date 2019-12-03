#!/usr/bin/env bash

# Utility to ingest successfully a file
function lega_ingest {
    local TESTFILE=$1
    local size=$2 # in MB
    local queue=$3
    local inputsource=${4:-/dev/urandom}

    [ -n "${TESTUSER}" ]
    [ -n "${TESTUSER_SECKEY}" ]
    [ -n "${TESTUSER_PASSPHRASE}" ]

    # Create a random file of { size } MB
    legarun c4gh_generate ${size} ${TESTFILES}/${TESTFILE} ${TESTUSER_SECKEY} ${TESTUSER_PASSPHRASE}
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

    # Check that a message with the above correlation id arrived in the expected queue
    # Waiting 200 seconds.
    retry_until 0 20 10 ${MQ_GET} $queue "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
}