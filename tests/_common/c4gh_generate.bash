#!/usr/bin/env bash

# Generate a file of size from the $infile file (/dev/zero, or /dev/urandom)
# and places the output in $outfile.c4ga
function c4gh_generate {
    local size=$1
    local infile=$2
    local outfile=$3
 
    # # Create a file of {size} MB
    # legarun dd if=$infile of=$outfile count=$size bs=1048576
    # [ "$status" -eq 0 ]

    # # Encrypt it in the Crypt4GH format
    # legarun lega-cryptor encrypt --pk ${EGA_PUB_KEY} -i ${outfile} -o ${outfile}.c4ga
    # [ "$status" -eq 0 ]

    size=$((size * 1048576))
    python ${HERE}/c4gh_generate.py $size ${EGA_PUB_KEY} -i $infile -o ${outfile}.c4ga
}
