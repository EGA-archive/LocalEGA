#!/usr/bin/env bats

load ../_common/helpers

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

# Malformed messages
# ------------------
# Message published at Central EGA but malformed
# are sent to the error queue

@test "Message malformed from CentralEGA" {

    TESTFILE=$(uuidgen)
    TESTFILE_ENCRYPTED="${TESTFILES}/${TESTFILE}.c4gh"
    TESTFILE_UPLOADED="/${TESTFILE}.c4gh"

    lega_generate_file ${TESTFILE} ${TESTFILE_ENCRYPTED} 1 /dev/zero
    lega_upload "${TESTFILE_ENCRYPTED}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET_INBOX} "${TESTUSER}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger, but with a malformed message (not in JSON)
    MESSAGE="user: ${TESTUSER}\nfilepath: ${TESTFILE_UPLOADED}"
    legarun ${MQ_PUBLISH} --correlation_id "${CORRELATION_ID}" files "$MESSAGE"
    [ "$status" -eq 0 ]

    retry_until 0 30 10 ${MQ_FIND} v1.files.error "${CORRELATION_ID}"
    [ "$status" -eq 0 ]

    [[ "$output" =~ "reason: " ]]
    [[ "$output" =~ "Malformed JSON-message" ]]

}


# MQ federated queue
# ------------------
# Message published at Central EGA but local broker down for a while
# When restarted, no messages are lost

@test "MQ federation" {
    skip "Used after the update for MQ connection retries"
    
    TESTFILE=$(uuidgen)

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

    # Stop the local broker
    legarun docker stop mq

    # Publish the file to simulate a CentralEGA trigger
    MESSAGE="{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${TESTFILE}.c4ga\"}"
    legarun ${MQ_PUBLISH} --correlation_id ${CORRELATION_ID} files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Restart the local broker
    legarun docker start mq
    legarun sleep 20

    # Check that a message with the above correlation id arrived in the expected queue
    # Waiting 20 seconds.
    retry_until 0 10 2 ${MQ_GET} v1.files.completed "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]

}

# MQ restarted, test delivery mode
# --------------------------------
# Message published at Central EGA but local broker down for a while
# When restarted, no messages are lost

@test "MQ delivery mode" {
    skip "Used after the update for MQ connection retries"

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
    legarun docker stop mq
    legarun docker start mq
    legarun sleep 15

    # Check now that the delivery mode is still 2
    # And the messages are still there
    # Let it run its course
    
    # Restart verify
    legarun docker restart verify
    legarun sleep 15

    # Check that a message with the above correlation id arrived in the expected queue
    retry_until 0 10 2 ${MQ_GET} v1.files.completed "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
}
