#!/usr/bin/env bash

function echomsg {
    [[ -z "$VERBOSE" ]] && echo $@ && return 0
    if [[ "$VERBOSE" == 'yes' ]]; then
	echo -e "$@"
    else
	echo -n '.'
    fi
}

function task_complete {
    [[ -z "$VERBOSE" ]] && echo -e $@ && return 0
    if [[ $VERBOSE == 'yes' ]]; then
	echo -e "=> $1 \xF0\x9F\x91\x8D"
    else
	echo -e " \xF0\x9F\x91\x8D"
    fi
}


function backup {
    local target=$1
    if [[ -e $target ]] && [[ $FORCE != 'yes' ]]; then
	echomsg "Backing up $target"
	mv -f $target $target.$(date +"%Y-%m-%d_%H:%M:%S")
    fi
}

function rm_politely {
    local FOLDER=$1
 
    if [[ -d $FOLDER ]]; then
	if [[ $FORCE == 'yes' ]]; then
	    rm -rf $FOLDER
	else
	    # Asking
	    echo "[Warning] The folder \"$FOLDER\" already exists. "
	    while : ; do # while = In a subshell
		echo -n "[Warning] "
		echo -n -e "Proceed to re-create it? [y/N] "
		read -t 10 yn
		case $yn in
		    y) rm -rf $FOLDER; break;;
		    N) echo "Ok. Choose another private directory. Exiting"; exit 1;;
		    *) echo "Eh?";;
		esac
	    done
	fi
    fi
}

function generate_password {
    local force=${2:-no}
    if [[ "${force}" != "force" ]] && [[ "${DEPLOY_DEV}" = "yes" ]]; then
	echo "dummy"
	return 0 # early return
    fi
    # Otherwise
    local size=${1:-16} # defaults to 16 characters
	${PYTHONEXEC} $HERE/pass_gen.py "$1"
}

function generate_mq_hash {
    local pass=${1}
    [[ -n $1 ]] || { echo 'Missing argument' 1>&2; exit 1; }  # fail
    ${PYTHONEXEC} $HERE/mq_hash.py "$1"
}


function check_python_module {
    local module=${1}
    ${PYTHONEXEC} -c "import ${module}" > /dev/null 2>&1
    retval=$?
    # do_something $retval
    if [ $retval -ne 0 ]; then
        echo "${module} is required and is missing."
        exit 1
    fi
}

function url_encode {
    local domain=${1}
	local option=${2}
    [[ -n $1 ]] || { echo 'Missing domain' 1>&2; exit 1; }  # fail
	[[ -n $2 ]] || { echo 'Missing option' 1>&2; exit 1; }  # fail
    ${PYTHONEXEC} $HERE/url_encode.py "$1" "$2"
}


function do_user_credentials {
	local user=${1}
	echomsg "\t\t - User ${user}"
	pushd ../../deploy/ &>/dev/null
	passphrase=$(generate_password 8)
	popd &>/dev/null
	PASSPHRASES[$user]=$passphrase
	rm -rf $user
	ssh-keygen -t ed25519 -f ${USERS_DIR}/$user -N "$passphrase" -C "$user"@LocalEGA &>/dev/null
	pubkey=$(cat ${USERS_DIR}/${user}.pub)
	uid=${USERS[${user}]}
	${PYTHONEXEC} ../../deploy/$HERE/user_data.py "$passphrase" "$user" "$uid" "$pubkey" "${USERS_DIR}"
}