#!/usr/bin/env bats

load ../helpers

TESTUSER=dummy

function setup() {

    # Changing the LOG file location
    DEBUG_LOG=$BATS_TEST_DIRNAME/output.debug

    # Defining the TMP dir
    TESTFILES=$BATS_TEST_DIRNAME/tmpfiles

    # Run only for the first test
    if [[ "$BATS_TEST_NUMBER" -eq 1 ]]; then
	rm -rf ${DEBUG_LOG}

	# Check if the Environment Variables exist
	if [ -z ${TESTUSER_SSHKEY+x} ]; then echo "TESTUSER_SSHKEY is unset"; exit 2; fi
	if [ -z ${CEGA_CONNECTION+x} ]; then echo "CEGA_CONNECTION is unset"; exit 2; fi

	# We need Connections to Central EGA
	if ! command -v sftp &>/dev/null; then echo "sftp command not found"; exit 2; fi
	#if ! command -v awk &>/dev/null; then echo "awk command not found"; exit 2; fi
	#if ! command -v curl &>/dev/null; then echo "curl command not found"; exit 2; fi

	# run curl https://egatest.crg.eu/lega/v1/legas/users/${TESTUSER}?idType=username
	# [ "$status" -eq 0 ]

	# Creating a TMP directory
	mkdir -p "$TESTFILES"
	echo "${TESTUSER_SSHKEY}" > $TESTFILES/testuser.sshkey
	chmod 400 $TESTFILES/testuser.sshkey
    fi

}

function teardown() {
    # Remove after the last test
    if [[ "$BATS_TEST_NUMBER" -eq "${#BATS_TEST_NAMES[@]}" ]]; then
	rm -rf "$TESTFILES"
    fi
}

@test "Ingesting properly a 10MB file" {

    # Create a random file of 10 MB
    legarun dd if=/dev/urandom of=${TESTFILES}/${BATS_TEST_NAME} count=10 bs=1048576
    [ "$status" -eq 0 ]

    # Encrypt it in the Crypt4GH format
    legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${BATS_TEST_NAME} -o ${TESTFILES}/${BATS_TEST_NAME}.c4ga
    [ "$status" -eq 0 ]

    # Upload it
    legarun sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INSTANCE_PORT} -i ${TESTFILES}/testuser.sshkey ${TESTUSER}@localhost <<< $"put ${TESTFILES}/${BATS_TEST_NAME}.c4ga /${BATS_TEST_NAME}.c4ga"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: use the path)
    legarun get_shasum ${TESTFILES}/${BATS_TEST_NAME}.c4ga
    [ "$status" -eq 0 ]
    legarun python ${MAIN_REPO}/extras/rabbitmq_get.py --connection ${CEGA_CONNECTION} v1.files.inbox $output
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    legarun python ${MAIN_REPO}/extras/cega_publish.py --connection ${CEGA_CONNECTION} --correlation_id ${CORRELATION_ID} 'files' "{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${BATS_TEST_NAME}.c4ga\"}" 
    [ "$status" -eq 0 ]


    # Check that a message with the above correlation id arrived in the completed queue
    retry_until 0 10 1 python ${MAIN_REPO}/extras/rabbitmq_find.py --connection ${CEGA_CONNECTION} v1.files.completed ${CORRELATION_ID}
    [ "$status" -eq 0 ]
}

@test "Ingesting properly a 100MB file" {

    # Create a random file of 100 MB
    legarun dd if=/dev/urandom of=${TESTFILES}/${BATS_TEST_NAME} count=100 bs=1048576
    [ "$status" -eq 0 ]

    # Encrypt it in the Crypt4GH format
    legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${BATS_TEST_NAME} -o ${TESTFILES}/${BATS_TEST_NAME}.c4ga
    [ "$status" -eq 0 ]

    # Upload it
    legarun sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INSTANCE_PORT} -i ${TESTFILES}/testuser.sshkey ${TESTUSER}@localhost <<< $"put ${TESTFILES}/${BATS_TEST_NAME}.c4ga /${BATS_TEST_NAME}.c4ga"
    [ "$status" -eq 0 ]

    # Fetch the correlation id for that file (Hint: use the path)
    legarun get_shasum ${TESTFILES}/${BATS_TEST_NAME}.c4ga
    [ "$status" -eq 0 ]
    legarun python ${MAIN_REPO}/extras/rabbitmq_get.py --connection ${CEGA_CONNECTION} v1.files.inbox $output
    [ "$status" -eq 0 ]
    CORRELATION_ID=$output

    # Publish the file to simulate a CentralEGA trigger
    legarun python ${MAIN_REPO}/extras/cega_publish.py --connection ${CEGA_CONNECTION} --correlation_id ${CORRELATION_ID} 'files' "{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${BATS_TEST_NAME}.c4ga\"}" 
    [ "$status" -eq 0 ]


    # Check that a message with the above correlation id arrived in the completed queue
    retry_until 0 10 1 python ${MAIN_REPO}/extras/rabbitmq_find.py --connection ${CEGA_CONNECTION} v1.files.completed ${CORRELATION_ID}
    [ "$status" -eq 0 ]
}
