#!/usr/bin/env bats

load ../helpers

function setup() {

	if [[ "$BATS_TEST_NUMBER" -eq 1 ]]; then
		TESTFILES=$BATS_TEST_DIRNAME/tmpfiles_auth
		echo "Creating Tmp files in $TESTFILES"
		mkdir -p "$TESTFILES"

		DOCKER_PATH=$BATS_TEST_DIRNAME/../../deploy
		EGA_PUB_KEY=${DOCKER_PATH}/private/lega/pgp/ega.pub
		
		JANE_PRIV_KEY=${DOCKER_PATH}/private/cega/users/jane.sec
		SSHFAKEKEY="-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAQEAxxEOk25jN2WGg0j21iIwPr05+Ne+yowRYnxBRYg48x5vRW2gDM2R
WCro9vE3ulThpbp+pvjIozJPlQ7/5Q1EdtZmyf6ReENKzCyVG0OPVDTAl5RUCyuYGoDD/r
+51LHTKIQS62baySfJGdhbAjN6nmxVMFiJzTR5FE3kmw5oNvD6wziHZuojxNM7nIyJjmX+
we0mxS5GEEwgz0dV8h1DJh5b/UwxmoODPyTLQjT4O18i+x9zhu10pS0UahTXiTB0a6q9aw
R/9LjvXUhL279Ul7tCO5Ke+uSrkydnc1f+yO4x6/a6sOHo7vDDIqn+yho3jZ+vJfSyDClm
gh/AXr4T2QAAA9DcVo693FaOvQAAAAdzc2gtcnNhAAABAQDHEQ6TbmM3ZYaDSPbWIjA+vT
n4177KjBFifEFFiDjzHm9FbaAMzZFYKuj28Te6VOGlun6m+MijMk+VDv/lDUR21mbJ/pF4
Q0rMLJUbQ49UNMCXlFQLK5gagMP+v7nUsdMohBLrZtrJJ8kZ2FsCM3qebFUwWInNNHkUTe
SbDmg28PrDOIdm6iPE0zucjImOZf7B7SbFLkYQTCDPR1XyHUMmHlv9TDGag4M/JMtCNPg7
XyL7H3OG7XSlLRRqFNeJMHRrqr1rBH/0uO9dSEvbv1SXu0I7kp765KuTJ2dzV/7I7jHr9r
qw4eju8MMiqf7KGjeNn68l9LIMKWaCH8BevhPZAAAAAwEAAQAAAQEAsPETYK61GA9xIg7g
APRAp/OwrOSwHP+lkEHcDr8Hx+ocg7zuj5LFh3YUvzMoEsLSE2qSmz31sUHOBTNg96r0WS
E4GoHhseE2ggd6vdIue22sZs+caJVmTOB51l17A3jQtWm4G2/ANx7bHNL4ChvR+TFYA3If
grwKh6a49a43qeS112zg+WiaZH4z91AQvhknS8tDvcoXVio9L6URa5FVh5C6wmyyWNW3wJ
K3daY6+OqEq3m1EOsiEfhQfpxqvhXZzCoNNp2Hx9geOXkPrX4FAe4VUTlQmXGyY6mcyNYR
IXjDrjBKxymBR6BU3Y5G2bJAE9CBXb9SL6JfPZlYtf+rgQAAAIBhvll1EcWxwmG5NNDwdm
05g7ds5TxFfcjaEYbclRfCr4pSr0m+1tE1UoCfh+JQHqoslICfGmMVAoeCWC8xfPRXOeJh
ePD7XzIuPwStyTLhnfXpDEijg/dIm+vA3hqp8oklBEwD7/WveOhLnJKHB3LGvhQ2o6QEu+
1Hp77SFaRGqAAAAIEA5JFaIWotglhVcRunh6LgvHixL7OypVZCDpYUU0fP2ulTJMPJWc6L
FO4f64FiJ9/q1C5A8B3HJVFY428zEOK1EdzM8UrpQQjKXNNKpVi9YeOJdA2pAVdpUWBvRr
dioW1ND6/9sImiDpTOCLCQ7e64+5Wn/+HRaDywBQbgi0xAs/EAAACBAN71S2M/hhb6w8Kc
5Z9cbpt4hbacs3BifdQTPwVIGef599C5SYQe7E23REVOlQyTfO6P/AMVwaNMqfhbCWRXI4
qX0IPhF9IVLQhsFYsYfNdtOtJzFwa00Ty4yBiRKO1MC+sC+qOzECkZSTE5XNnjnWpL5LrW
CmyAdfQakScJ5qZpAAAAE29tYXJ0aW5lekA0ZjA2ODU4OWgBAgMEBQYH
-----END OPENSSH PRIVATE KEY-----"
		
		echo "${SSHFAKEKEY}" > $TESTFILES/fake.sshkey
		chmod 400 $TESTFILES/fake.sshkey
	fi
}

function teardown() {
	if [[ "${#BATS_TEST_NAMES[@]}" -eq "$BATS_TEST_NUMBER" ]]; then
		rm -rf "$BATS_TEST_DIRNAME/tmpfiles_auth"
	fi
}

@test "Ingest a file with a user that does not exist in CentralEGA" {
	TESTUSER=nonexistant
    legarun dd if=/dev/urandom of=${TESTFILES}/${BATS_TEST_NAME} count=10 bs=1048576
    legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${BATS_TEST_NAME} -o ${TESTFILES}/${BATS_TEST_NAME}.c4ga
	#-oBatchMode=yes for not prompting password
    run sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -oBatchMode=yes -P ${INSTANCE_PORT} ${TESTUSER}@localhost
    [ "$status" -eq 255 ]
	#Remove carriage return
	line_to_compare=$(echo ${lines[2]} | tr -d '\r')
	[ "${line_to_compare}" = "${TESTUSER}@localhost: Permission denied (publickey,keyboard-interactive)." ]
}

@test "Ingest a file with a user in CentralEGA, using the wrong password" {
	skip "We have to see how to pass a password to sftp server, sshpass, expect..."
	TESTUSER=jane
	USER_PASS=nonsense_password
    legarun dd if=/dev/urandom of=${TESTFILES}/${BATS_TEST_NAME} count=10 bs=1048576
    legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${BATS_TEST_NAME} -o ${TESTFILES}/${BATS_TEST_NAME}.c4ga
	lftp -u $TESTUSER,$USER_PASS sftp://localhost:${INSTANCE_PORT} << --EOF--
ls
quit
--EOF--
    #run sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INSTANCE_PORT} ${TESTUSER}@localhost
    [ "$status" -eq 255 ]
	#Remove carriage return
	line_to_compare=$(echo ${lines[2]} | tr -d '\r')
	[ "${line_to_compare}" = "${TESTUSER}@localhost: Permission denied (publickey,keyboard-interactive)." ]
}

@test "Ingest a file with a user in CentralEGA using the wrong sshkey" {
	TESTUSER=jane
    legarun dd if=/dev/urandom of=${TESTFILES}/${BATS_TEST_NAME} count=10 bs=1048576
    legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${TESTFILES}/${BATS_TEST_NAME} -o ${TESTFILES}/${BATS_TEST_NAME}.c4ga
	#-oBatchMode=yes for not prompting password
	run sftp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P ${INSTANCE_PORT} -i {$TESTFILES/fake.sshkey} -oBatchMode=yes ${TESTUSER}@localhost
    [ "$status" -eq 255 ]
	#Remove carriage return
	line_to_compare=$(echo ${lines[3]} | tr -d '\r')
	[ "${line_to_compare}" = "${TESTUSER}@localhost: Permission denied (publickey,keyboard-interactive)." ]
}