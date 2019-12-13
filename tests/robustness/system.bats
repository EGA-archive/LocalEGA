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

    # Find inbox port mapping. Usually 2222:9000
    INBOX_PORT="2222"
    # legarun docker port inbox 9000
    # [ "$status" -eq 0 ]
    # INBOX_PORT=${output##*:}
}

function teardown() {
    rm -rf ${TESTFILES}
}

# Whole system restart
# --------------------
# Ingest a file, restart every component, ingest another file

@test "Whole system restart" {
    skip "Used after the update for notification connection retries"

    lega_ingest $(uuidgen) 1 v1.files.completed

    pushd ../deploy
    legarun docker-compose restart
    legarun make preflight-check
    popd

    lega_ingest $(uuidgen) 2 v1.files.completed
}
