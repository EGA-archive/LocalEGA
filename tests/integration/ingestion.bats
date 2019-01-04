#!/usr/bin/env bats

load helpers


TESTUSER=john

function setup() {

    # Check if the Environment Variables exist
    if [ -z ${TESTUSER_SSHKEY+x} ]; then echo "TESTUSER_SSHKEY is unset"; exit 2; fi
    if [ -z ${CEGA_CONNECTION+x} ]; then echo "CEGA_CONNECTION is unset"; exit 2; fi

    # We need Connections to Central EGA
    if ! command -v sftp &>/dev/null; then echo "sftp command not found"; exit 2; fi
    #if ! command -v awk &>/dev/null; then echo "awk command not found"; exit 2; fi
    #if ! command -v curl &>/dev/null; then echo "curl command not found"; exit 2; fi

    # run curl https://egatest.crg.eu/lega/v1/legas/users/${TESTUSER}?idType=username
    # [ "$status" -eq 0 ]

    TESTFILES=$BATS_TEST_DIRNAME/tmpfiles
    echo "Creating Tmp files in $TESTFILES"
    mkdir -p "$TESTFILES"
    echo "${TESTUSER_SSHKEY}" > $TESTFILES/testuser.sshkey
    chmod 400 $TESTFILES/testuser.sshkey

    DOCKER_PATH=$BATS_TEST_DIRNAME/../../deploy
    EGA_PUB_KEY=${DOCKER_PATH}/private/lega/pgp/ega.pub

    # Find inbox port mapping. Usually 2222:9000
    run docker port inbox 9000
    INSTANCE_PORT=${output##*:}
    echo_output "Docker inbox port: ${INSTANCE_PORT}"

}

function teardown() {
    rm -rf "$TESTFILES"
}

@test "Ingesting properly a 10MB file" {
    TESTFILE=
    run dd if=/dev/urandom of=${TESTFILES}/${BATS_TEST_NAME} count=10 bs=1048576
    run lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${BATS_TEST_NAME} -o ${TESTFILES}/${BATS_TEST_NAME}.c4ga
    run pushd ${TESTFILES}
    run sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INSTANCE_PORT} -i ${TESTFILES}/testuser.sshkey ${TESTUSER}@localhost <<< $"put ${BATS_TEST_NAME}.c4ga"
    echo_output "SFTP: ${BATS_TEST_NAME}.c4ga"
    run popd
    # For CEGA_CONNECTION
    source ${DOCKER_PATH}/private/lega/mq.env
    CEGA_CONNECTION=${CEGA_CONNECTION//cega-mq/localhost}

    run python ${MAIN_REPO}/extras/cega_publish.py --connection ${CEGA_CONNECTION} 'files' "{ \"user\": \"${TESTUSER}\", \"filepath\": \"/${BATS_TEST_NAME}.c4ga\"}"

    echo_output "Publish message to MQ"
    echo_status "Publish message to MQ"

    # TODO: check the rabbitMQ completed queue + finalize

    [ "$status" -eq 0 ]
}



