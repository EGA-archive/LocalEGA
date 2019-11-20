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
    if ! ${PYTHONEXEC} -c 'import importlib; import sys; sys.exit(0 if importlib.util.find_spec("bcrypt") is not None else 1)'; then
	echo 'The python bcrypt package is not found for this python version'
	exit 1
    fi

    # Generate key with passphrase for all users
    for user in ${!USERS[@]}
    do
	echomsg "\t\t - User ${user}"
	passphrase=$(generate_password 8)
	PASSPHRASES[$user]=$passphrase
	rm -rf $user
	ssh-keygen -t ed25519 -f ${USERS_DIR}/$user -N "$passphrase" -C "$user"@LocalEGA &>/dev/null
	
	# Bcrypt hash
	passphrase_hash=$(echo -n $passphrase | \
	${PYTHONEXEC} -c 'import bcrypt; import sys; sys.stdout.buffer.write(bcrypt.hashpw(sys.stdin.buffer.read(), bcrypt.gensalt()))')

	cat > ${USERS_DIR}/${user}.json <<EOF
{
	"username" : "${user}",
	"uid" : ${USERS[${user}]},
	"passwordHash" : "${passphrase_hash}",
        "gecos" : "LocalEGA user ${user}",
  	"sshPublicKey" : "$(cat ${USERS_DIR}/${user}.pub)",
	"enabled" : null
}
EOF
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
