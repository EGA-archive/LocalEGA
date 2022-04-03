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

    # echo "TESTUSER KEY: $TESTUSER_SECKEY"
    # echo "TESTUSER PASSPHRASE: $TESTUSER_PASSPHRASE"

    # Find inbox port mapping. Usually 2222:9000
    INBOX_PORT="2222"
    # legarun docker port inbox 9000
    # [ "$status" -eq 0 ]
    # INBOX_PORT=${output##*:}

    ARCHIVE_DB_PORT="15432"
}

function teardown() {
    rm -rf ${TESTFILES}

    # Kill an SSH-agent for this env
    [[ -n "${SSH_AGENT_PID}" ]] && kill -TERM "${SSH_AGENT_PID}"
}

# Ingesting a 1 MB file
# ----------------------
# A message should be found in the completed queue

@test "Ingest properly a test file, with a dataset mapping" {

    local FILENAME=$(uuidgen)
    lega_ingest ${FILENAME} 1 v1.files.completed /dev/urandom
    [ "$status" -eq 0 ]

    # Find the accession_id in archive-db
    run docker-compose exec -e PGPASSWORD=$(<private/secrets/archive-db.lega) archive-db \
                       psql -h localhost -U lega -d lega --csv -q -t -c \
		       "select accession_id from local_ega.main where inbox_path LIKE '%${FILENAME}%';"

    DATASET="EGAD00000000001" # forcing Dataset 1
    ACCESSION=$(echo $output | tr -d '\r\n')
    cat > ${TESTFILES}/message.json <<EOF
{
 "type": "mapping",
 "dataset_id": "$DATASET",
 "accession_ids": ["$ACCESSION"]
}
EOF

    # Publish the file to simulate a CentralEGA mapping
    #legarun ${MQ_PUBLISH} --correlation_id $(uuidgen) mapping "$(<${TESTFILES}/message.json)"
    legarun ${MQ_PUBLISH} mapping "$(<${TESTFILES}/message.json)"
    [ "$status" -eq 0 ]

    run sleep 5

    # Check if the message is in the database
    run docker-compose exec -e PGPASSWORD=$(<private/secrets/archive-db.lega) archive-db \
                       psql -h localhost -U lega -d lega --csv -q -t -c \
		       "select * from local_ega.main where accession_id = '${ACCESSION}' AND dataset_id = '${DATASET}';"
    [ "$status" -eq 0 ]
    [ ${#lines[@]} -ge 1 ]
}
