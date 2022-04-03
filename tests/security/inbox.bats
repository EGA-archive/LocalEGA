#!/usr/bin/env bats
# -*- mode:shell-script -*-

load ../_common/helpers

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
    load_into_ssh_agent jane
    [[ $? != 0 ]] && echo "Error loading jane into the local ssh-agent" >&2 && exit 3
    load_into_ssh_agent john
    [[ $? != 0 ]] && echo "Error loading john into the local ssh-agent" >&2 && exit 3

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

# Inbox isolation
# ---------------
# Users should somehow be chrooted in their own home directory

@test "A user can not access the files of another user" {

    # Create a file
    JANE_FILE=${TESTFILES}/jane.secret
    SECRET=$(date)
    echo ${SECRET} > ${JANE_FILE}

    # Upload the file
    legarun ${LEGA_SFTP} jane@localhost <<< "put ${JANE_FILE} /my.secret"
    [ "$status" -eq 0 ]

    # Can John spy on Jane ?
    legarun ${LEGA_SFTP} john@localhost <<< "get ../jane/my.secret ${TESTFILES}/jane.secret.for.john"

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
    legarun ${LEGA_SFTP} jane@localhost <<< "put ${JANE_FILE} /my.secret"
    [ "$status" -eq 0 ]

    # Can John spy on Jane ?
    # Hard-coding the absolute path in that test, since /ega/inbox/<username> is what we use
    # Ideally, this path is hidden (even more true if the backend is S3)
    legarun ${LEGA_SFTP} john@localhost <<< "get /ega/inbox/jane/my.secret ${TESTFILES}/jane.secret.for.john.2"

    if [[ -e ${TESTFILES}/jane.secret.for.john.2 ]]; then
    	[ "$SECRET" -eq "$(<${TESTFILES}/jane.secret.for.john.2)" ]
    fi
    [ "$status" -eq 0 ]
}

