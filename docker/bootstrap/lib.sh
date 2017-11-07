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

function rabbitmq_hash {
    # 1) Generate a random 32 bit salt
    # 2) Concatenate that with the UTF-8 representation of the password
    # 3) Take the SHA-256 hash
    # 4) Concatenate the salt again
    # 5) Convert to base64 encoding
    local SALT=${2:-$(${OPENSSL:-openssl} rand -hex 4)}
    (
	printf $SALT | xxd -p -r
	( printf $SALT | xxd -p -r; printf $1 ) | ${OPENSSL:-openssl} dgst -binary -sha256
    ) | base64
}


function join_by { local IFS="$1"; shift; echo -n "$*"; }
