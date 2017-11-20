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
    local size=${1:-16} # defaults to 16 characters
    p=$(python3.6 -c "import secrets,string;print(''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(${size})))")
    echo $p
}

