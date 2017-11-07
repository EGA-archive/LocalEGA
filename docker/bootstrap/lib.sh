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


function print_arr {
    for x in "${!1[@]}"; do printf "[%s]=%s " "$x" "${array[$x]}" ; done
}

function join_by { local IFS="$1"; shift; echo -n "$*"; }
