#!/usr/bin/env bash

# Generate a file of size from the /dev/urandom
# and places the output in $outfile.c4ga
function c4gh_generate {
    local size=$1
    local outfile=$2
    local seckey=$3
    local pass=$4
 
    size=$((size * 1048576))
    legarun dd if=/dev/urandom of=${outfile} count=1 bs=${size}
    [ "$status" -eq 0 ]
    
    export C4GH_PASSPHRASE=${pass}
    crypt4gh encrypt --sk ${seckey} --recipient_pk ${EGA_PUBKEY} < ${outfile} > ${outfile}.c4ga
    unset C4GH_PASSPHRASE
}
