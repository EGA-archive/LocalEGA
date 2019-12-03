#!/usr/bin/env bats

load ../_common/helpers
load ../_common/c4gh_generate
load ../_common/ingest

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

# Ingestion after db restart
# --------------------------
# Ingest a file, stop db, start db, ingest another file

@test "Ingestion after db restart" {
    skip "Used after the update for DB connection retries"

    lega_ingest $(uuidgen) 1 v1.files.completed
    legarun docker stop localega-db.default
    legarun docker start localega-db.default
    legarun sleep 15
    lega_ingest $(uuidgen) 1 v1.files.completed

}

# DB restart in the middle of ingestion
# -------------------------------------

@test "DB restart in the middle of ingestion" {
    # skip "Used after the update for DB connection retries"

    TESTFILE=$(uuidgen)
    [ -n "${TESTUSER}" ]
    [ -n "${TESTUSER_SECKEY}" ]
    [ -n "${TESTUSER_PASSPHRASE}" ]

    # Stop the verify component, so only ingest works
    legarun docker stop verify.default

    # Create a random file Crypt4GH file of 1 MB
    legarun c4gh_generate 1 ${TESTFILES}/${TESTFILE} ${TESTUSER_SECKEY} ${TESTUSER_PASSPHRASE}
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
    legarun docker stop localega-db.default
    legarun docker start localega-db.default
    legarun sleep 15

    # Restart verify
    legarun docker restart verify.default
    legarun sleep 15

    # Check that a message with the above correlation id arrived in the expected queue
    retry_until 0 10 2 ${MQ_GET} v1.files.completed "${TESTUSER}" "/${TESTFILE}.c4ga"
    [ "$status" -eq 0 ]
}
