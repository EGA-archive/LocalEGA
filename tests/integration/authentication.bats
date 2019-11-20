#!/usr/bin/env bats

load ../_common/helpers

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

@test "Ingest a file for a user that does not exist in CentralEGA" {

    legarun ${LEGA_SFTP} -oBatchMode=yes nonexistant@localhost <<< $"ls"
    # -oBatchMode=yes for not prompting password
    [ "$status" -eq 255 ]
    #[[ "${lines[2]}" == *"Permission denied"* ]]
    [[ "${output}" == *"Permission denied"* ]]
}

@test "Ingest a file using the wrong user password" {
    skip "We have to see how to pass a password to sftp server, sshpass, expect..."

    TESTUSER=jane
    USER_PASS=nonsense_password

    legarun lftp -u $TESTUSER,$USER_PASS sftp://localhost:${INBOX_PORT} <<< $"ls"
    #run ${LEGA_SFTP} ${TESTUSER}@localhost
    [ "$status" -eq 255 ]
    #[[ "${lines[2]}" == *"Permission denied"* ]]
    [[ "${output}" == *"Permission denied"* ]]
}

@test "Ingest a file using the wrong user sshkey" {

    TESTUSER=jane
    ssh-keygen -f $TESTFILES/fake.sshkey -N ''
    chmod 400 $TESTFILES/fake.sshkey

    legarun ${LEGA_SFTP} -oBatchMode=yes -i $TESTFILES/fake.sshkey ${TESTUSER}@localhost
    # -oBatchMode=yes for not prompting password
    [ "$status" -eq 255 ]
    #[[ "${lines[2]}" == *"Permission denied"* ]]
    [[ "${output}" == *"Permission denied"* ]]
}
