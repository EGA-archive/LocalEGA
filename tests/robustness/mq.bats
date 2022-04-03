#!/usr/bin/env bats
# -*- mode:shell-script -*-

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

    [[ "$output" =~ "informal: " ]]
    [[ "$output" =~ "Malformed JSON-message" ]]

}


# MQ federated queue
# ------------------
# Message published at Central EGA but local broker down for a while
# When restarted, no messages are lost

@test "MQ federation" {

    TESTFILE=$(uuidgen)
    TESTFILE_ENCRYPTED="${TESTFILES}/${TESTFILE}.c4gh"
    TESTFILE_UPLOADED="/${TESTFILE}.c4gh"

    # Create a random file Crypt4GH file of 1 MB
    lega_generate_file ${TESTFILE} ${TESTFILE_ENCRYPTED} 1 /dev/urandom

    # Upload it
    lega_upload "${TESTFILE_ENCRYPTED}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET_INBOX} "${TESTUSER}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Stop the local broker
    legarun docker stop mq
    [ "$status" -eq 0 ]

    # Publish the file to simulate a CentralEGA trigger, but with a malformed message (not in JSON)
    MESSAGE="{ \"type\": \"ingest\", \"user\": \"${TESTUSER}\", \"filepath\": \"${TESTFILE_UPLOADED}\"}"
    legarun ${MQ_PUBLISH} --correlation_id "${CORRELATION_ID}" files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Restart the local broker
    legarun docker start mq
    sleep 20 # is it enough?
    
    # Check that a message with the above correlation id arrived in the expected queue
    retry_until 0 30 10 ${MQ_FIND} v1.files.completed "${CORRELATION_ID}"
    [ "$status" -eq 0 ]

}

# MQ restarted, test delivery mode
# --------------------------------
# Message published at Central EGA but local broker down for a while
# When restarted, no messages are lost

@test "MQ delivery mode" {

    TESTFILE=$(uuidgen)
    TESTFILE_ENCRYPTED="${TESTFILES}/${TESTFILE}.c4gh"
    TESTFILE_UPLOADED="/${TESTFILE}.c4gh"

    # Stop the verify component, so only ingest works
    legarun docker stop verify

    # Create a random file Crypt4GH file of 1 MB
    lega_generate_file ${TESTFILE} ${TESTFILE_ENCRYPTED} 1 /dev/urandom

    # Upload it
    lega_upload "${TESTFILE_ENCRYPTED}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET_INBOX} "${TESTUSER}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Stop the local broker
    legarun docker stop mq
    [ "$status" -eq 0 ]

    # Publish the file to simulate a CentralEGA trigger, but with a malformed message (not in JSON)
    MESSAGE="{ \"type\": \"ingest\", \"user\": \"${TESTUSER}\", \"filepath\": \"${TESTFILE_UPLOADED}\"}"
    legarun ${MQ_PUBLISH} --correlation_id "${CORRELATION_ID}" files "$MESSAGE"
    [ "$status" -eq 0 ]

    # Restart database
    legarun docker stop mq
    legarun docker start mq
    [ "$status" -eq 0 ]
    sleep 15
    
    # Check now that the delivery mode is still 2
    # And the messages are still there
    # Let it run its course
    
    # Restart the ingest microservice
    legarun docker restart ingest
    sleep 15

    # Check that a message with the above correlation id arrived in the expected queue
    retry_until 0 30 10 ${MQ_FIND} v1.files.completed "${CORRELATION_ID}"
    [ "$status" -eq 0 ]
}


# MQ federated shovel
# -------------------
# Message published to Central EGA via the shovel are not lost if the central broker down for a while
# When restarted, no messages are lost

@test "MQ federation - shovel" {

    TESTFILE=$(uuidgen)
    TESTFILE_ENCRYPTED="${TESTFILES}/${TESTFILE}.c4gh"
    TESTFILE_UPLOADED="/${TESTFILE}.c4gh"

    # Create a random file Crypt4GH file of 1 MB
    lega_generate_file ${TESTFILE} ${TESTFILE_ENCRYPTED} 1 /dev/urandom

    # Upload it
    lega_upload "${TESTFILE_ENCRYPTED}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: with user/filepath combination)
    retry_until 0 100 1 ${MQ_GET_INBOX} "${TESTUSER}" "${TESTFILE_UPLOADED}"
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Stop the ingestion, this guarantees the ingestion won't complete
    legarun docker stop cleanup
    [ "$status" -eq 0 ]

    # Publish the file to simulate a CentralEGA trigger, but with a malformed message (not in JSON)
    MESSAGE="{ \"type\": \"ingest\", \"user\": \"${TESTUSER}\", \"filepath\": \"${TESTFILE_UPLOADED}\"}"
    legarun ${MQ_PUBLISH} --correlation_id "${CORRELATION_ID}" files "$MESSAGE"
    [ "$status" -eq 0 ]

    sleep 10 # and let it pass the accession step

    # Stop the central broker
    legarun docker stop cega-mq

    # Restart the ingestion, up to shovelling the completion message
    legarun docker start cleanup

    # Restart the central broker
    legarun docker start cega-mq
    sleep 10 # is it enough?
    
    # Check that a message with the above correlation id arrived in the expected queue
    retry_until 0 30 10 ${MQ_FIND} v1.files.completed "${CORRELATION_ID}"
    [ "$status" -eq 0 ]

}
