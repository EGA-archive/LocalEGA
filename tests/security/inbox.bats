#!/usr/bin/env bats

load ../_common/helpers

# CEGA_CONNECTION and CEGA_USERS_CREDS should be already set,
# when this script runs

function setup() {

    # Defining the TMP dir
    TESTFILES=${BATS_TEST_FILENAME}.d
    mkdir -p "$TESTFILES"

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

# Inbox isolation
# ---------------
# Users should somehow be chrooted in their own home directory

@test "A user can not access the files of another user" {

    # Create a file
    JANE_FILE=${TESTFILES}/jane.secret
    SECRET=$(date)
    echo ${SECRET} > ${JANE_FILE}

    # Upload the file
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/jane.sec jane@localhost <<< "put ${JANE_FILE} /my.secret"
    [ "$status" -eq 0 ]

    # Can John spy on Jane ?
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/john.sec john@localhost <<< "get ../jane/my.secret ${TESTFILES}/jane.secret.for.john"

    if [[ -e ${TESTFILES}/jane.secret.for.john ]]; then
    	[ "$SECRET" -eq "$(<${TESTFILES}/jane.secret.for.john)" ]
    fi
    [ "$status" -eq 0 ]
}

# Inbox isolation
# ---------------
# Users should somehow be chrooted in their own home directory
# "cd .." might be prevented by cutting/masking the path,
# but "cd <absolute-path>" outside of the home directory should not work

@test "A user can not access the files of another user via absolute path" {

    # Create a file
    JANE_FILE=${TESTFILES}/jane.secret
    SECRET=$(date)
    echo ${SECRET} > ${JANE_FILE}

    # Upload the file
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/jane.sec jane@localhost <<< "put ${JANE_FILE} /my.secret"
    [ "$status" -eq 0 ]

    # Can John spy on Jane ?
    # Hard-coding the absolute path in that test, since /ega/inbox/<username> is what we use
    # Ideally, this path is hidden (even more true if the backend is S3)
    legarun ${LEGA_SFTP} -i ${TESTDATA_DIR}/john.sec john@localhost <<< "get /ega/inbox/jane/my.secret ${TESTFILES}/jane.secret.for.john.2"

    if [[ -e ${TESTFILES}/jane.secret.for.john.2 ]]; then
    	[ "$SECRET" -eq "$(<${TESTFILES}/jane.secret.for.john.2)" ]
    fi
    [ "$status" -eq 0 ]
}

