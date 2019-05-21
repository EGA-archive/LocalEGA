#!/usr/bin/env bats

load ../_common/helpers
load ../_common/c4gh_generate

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Defining the TMP dir
    TESTFILES=${BATS_TEST_FILENAME}.d
    mkdir -p "$TESTFILES"

    # Test user
    TESTUSER=dummy

    # Find inbox port mapping. Usually 2222:9000
    INBOX_PORT="2222"
    # legarun docker port inbox 9000
    # [ "$status" -eq 0 ]
    # INBOX_PORT=${output##*:}
    LEGA_SFTP="sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INBOX_PORT}"
}

function teardown() {
    rm -rf ${TESTFILES}
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
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< $"put ${TESTFILES}/${TESTFILE}.c4ga /${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${TESTFILE}.c4ga\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID} files "$MESSAGE"
    [ "$status" -eq 0 ]

    # # Check that a message with the above correlation id arrived in the completed queue
    # retry_until 0 100 1 ${MQ_GET} v1.files.error "${TESTUSER}" "/${TESTFILE}.c4ga"
    # [ "$status" -eq 0 ]
}
