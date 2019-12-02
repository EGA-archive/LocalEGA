#!/usr/bin/env bats

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Defining the TMP dir
    TESTFILES=${BATS_TEST_FILENAME}.d
    mkdir -p $TESTFILES


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

    # Upload them (sshkey in agent already)
    legarun ${LEGA_SFTP} ${TESTUSER}@localhost <<< $"put -r ${TESTFILES}/batch"
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
    legarun dd if=/dev/zero of=${TESTFILES}/${TESTFILE} count=1 bs=1048576
    [ "$status" -eq 0 ]

    # Encrypt it in the Crypt4GH format
    export C4GH_PASSPHRASE=${TESTUSER_PASSPHRASE}
    crypt4gh encrypt --sk ${TESTUSER_SECKEY} --recipient_pk ${EGA_PUBKEY} < ${TESTFILES}/${TESTFILE} > ${TESTFILES}/${TESTFILE}.c4ga
    [ "$status" -eq 0 ]

    # Upload it
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/${TESTUSER}.sec ${TESTUSER}@localhost <<< $"put ${TESTFILES}/${TESTFILE}.c4ga ${TESTFILE}.c4ga"
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
