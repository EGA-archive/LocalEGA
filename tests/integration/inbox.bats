#!/usr/bin/env bats

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Defining the TMP dir
    TESTFILES=${BATS_TEST_FILENAME}.d
    mkdir -p $TESTFILES

    # Test user
    TESTUSER=dummy

    # Utilities to scan the Message Queues
    MQ_CONSUME="python ${MAIN_REPO}/extras/rabbitmq/consume.py --connection ${CEGA_CONNECTION}"
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

# Upload a batch of files
# -----------------------
#
# We "touch" 100 files spread in 10 directories and 10 subdirectories.
# We upload the top directory at once.
# That fires many "upload" messages at the inbox notification server.
# 100 messages should be found in the inbox queue for those files.

@test "Upload a batch of files" {

    # Generate the names
    mkdir -p ${TESTFILES}/batch/dir{1..10}/subdir{1..10}
    declare TESTFILES_NAMES=()
    for d in batch/dir{1..10}/subdir{1..10}
    do
	t=$d/$(uuidgen)
	touch ${TESTFILES}/$t # some empty files
	TESTFILES_NAMES+=( "/$t" )
    done

    # Upload them
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< $"put -r ${TESTFILES}/batch"
    [ "$status" -eq 0 ]

    # Find inbox messages for each file
    retry_until 0 100 1 ${MQ_CONSUME} v1.files.inbox ${TESTUSER} "${TESTFILES_NAMES[@]}"
    [ "$status" -eq 0 ]
}



# File not found in inbox
# -----------------------
#
# We upload a file, trigger an ingestion
# but the file was removed from the inbox
# We should receive a message in the error queue

@test "File not found in inbox goes to error" {

    TESTFILE=$(uuidgen)

    # Create a random file of {size} MB
    legarun dd if=/dev/urandom of=${TESTFILES}/${TESTFILE} count=1 bs=1048576
    [ "$status" -eq 0 ]

    # Encrypt it in the Crypt4GH format
    legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${TESTFILE} -o ${TESTFILES}/${TESTFILE}.c4ga
    [ "$status" -eq 0 ]

    # Upload it
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< $"put ${TESTFILES}/${TESTFILE}.c4ga /${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET} v1.files.inbox "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Remove the file
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< $"rm /${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${TESTFILE}.c4ga\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID} files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Check that a message with the above correlation id arrived in the expected queue
    # Waiting 20 seconds.
    retry_until 0 10 2 ${MQ_GET} v1.files.error "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]

}
