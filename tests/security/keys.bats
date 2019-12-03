#!/usr/bin/env bats

load ../_common/helpers

# Master key inaccessible from Inbox
# ----------------------------------
#
# Users logged in the inbox should not be able to retrive the decryption key
#
# Note: Even if the key is locked

@test "Unable to retrieve the decryption key from the inbox" {
    skip "Needs keyserver"

    PRIVATE_DATA=${MAIN_REPO}/deploy/private/pgp
    legarun python ${MAIN_REPO}/extras/get_pgp_keyid.py ${PRIVATE_DATA}/ega.sec $(<${PRIVATE_DATA}/ega2.sec.pass)
    KEY_ID=$output

    legarun docker exec inbox curl curl http://keys:8080/keys/retrieve/${KEY_ID}/private/bin?idFormat=hex 2>/dev/null
    [ -z "$output" ]
    [ $status -ne 0 ]
}
