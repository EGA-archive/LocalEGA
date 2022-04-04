#!/usr/bin/env bats
# -*- mode:shell-script -*-

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

# The name of the testfile can be ${BATS_TEST_NAME}, however, multiple runs of the testsuite
# would produce multiple message in the queues and the MQ_GET/MQ_FIND would get confused.
# We therefore use a uuid name, which can later be updated back to ${BATS_TEST_NAME}

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

# Ingesting a "big" file
# ----------------------
# A message should be found in the completed queue
#
# Note: We have tested with a 10 GB file by hand,
# and we are here 'only' ingesting a 1 GB file (for speed)
# Moreover, we are depleting the random pool,
# so we're using the /dev/zero for that particular test

@test "Ingest properly a 1GB file" {
    lega_ingest $(uuidgen) 1000 v1.files.completed /dev/zero
}
