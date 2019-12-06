#!/usr/bin/env bash

( # run in subshell
    set -e

    pushd ${HERE}/../../tests/_common &>/dev/null

    USERS_DIR=$(pwd)/users # includes expansion

    rm -rf ${USERS_DIR}
    mkdir -p ${USERS_DIR}

    declare -A USERS=([dummy]=15001 [john]=15002 [jane]=15003)
    declare -A PASSPHRASES

    # check that bcrypt is installed for this python version
    check_python_module bcrypt

    # Generate key with passphrase for all users
    for user in ${!USERS[@]}
    do
        do_user_credentials ${user}
    done


    # Recording the passphrase 
    # Custom format: username:private sshkey path:passphrase
    popd &>/dev/null
    echomsg "\t* Recording passphrases into .users"
    rm -rf ${PRIVATE}/.users
    for user in ${!USERS[@]}
    do
	echo "${user}:${USERS_DIR}/${user}:${PASSPHRASES[${user}]}" >> ${PRIVATE}/.users
    done

)
