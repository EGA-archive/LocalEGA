#!/usr/bin/env bats
# -*- mode:shell-script -*-

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

    cat > ${TESTFILES}/wrong_user.sh <<EOF
set timeout -1
spawn ${LEGA_SFTP} -oBatchMode=yes nonexistant@localhost

expect {
    "*sftp>*"                           { exit 1 }
    "Please, enter your EGA password: " { exit 2 }
    "*Permission denied*"               { exit 3 }
    "*Connection closed*"               { exit 3 }
    eof
}
EOF
    legarun expect -f ${TESTFILES}/wrong_user.sh &>/dev/null
    [ "$status" -eq 2 ] || [ "$status" -eq 3 ]

}

@test "Ingest a file using the wrong user password" {

    TESTUSER=jane
    USER_PASS=nonsense_password

    cat > ${TESTFILES}/sftp_password.sh <<EOF
set timeout -1
spawn ${LEGA_SFTP} ${TESTUSER}@localhost
expect "Please, enter your EGA password: "
send -- "${USER_PASS}\r"
expect "Please, enter your EGA password: "
send -- "${USER_PASS}\r"
expect "Please, enter your EGA password: "
send -- "${USER_PASS}\r"

expect {
    "*Permission denied*" { exit 2 }
    "*Connection closed*" { exit 2 }
    eof
}
EOF
    legarun expect -f ${TESTFILES}/sftp_password.sh &>/dev/null
    [ "$status" -eq 2 ]

    #rm -f ${TESTFILES}/sftp_password.sh
}

@test "Ingest a file using the wrong user sshkey" {

    TESTUSER=jane
    ssh-keygen -f $TESTFILES/fake.sshkey -N ''
    chmod 400 $TESTFILES/fake.sshkey
    
    cat > ${TESTFILES}/fake_key.sh <<EOF
set timeout -1
spawn ${LEGA_SFTP} -oBatchMode=yes -i ${TESTFILES}/fake.sshkey ${TESTUSER}@localhost
expect {
    "*sftp>*"                           { exit 1 }
    "Please, enter your EGA password: " { exit 2 }
    "*Permission denied*"               { exit 3 }
    "*Connection closed*"               { exit 3 }
    eof
}
EOF
    legarun expect -f ${TESTFILES}/fake_key.sh
    [ "$status" -eq 3 ]

    #rm -f ${TESTFILES}/fake_key.sh
}
