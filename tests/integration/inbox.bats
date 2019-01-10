#!/usr/bin/env bats

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Defining the TMP dir
    TESTFILES=${BATS_TEST_FILENAME}_tmpfiles
    mkdir -p $TESTFILES

    # Test user
    TESTUSER=dummy

    # Utilities to scan the Message Queues
    MQ_CONSUME="python ${MAIN_REPO}/extras/rabbitmq/consume.py --connection ${CEGA_CONNECTION}"

    # Find inbox port mapping. Usually 2222:9000
    legarun docker port inbox 9000
    [ "$status" -eq 0 ]
    INBOX_PORT=${output##*:}
    LEGA_SFTP="sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P $INBOX_PORT"
}

# function teardown() {
#     rm -rf ${TESTFILES}
# }

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
