#!/usr/bin/env bash
set -Eeo pipefail
# TODO swap to -Eeuo pipefail above (after handling all potentially-unset variables)

# Default paths
PG_SERVER_CERT=${PG_SERVER_CERT:-/etc/ega/pg.cert}
PG_SERVER_KEY=${PG_SERVER_KEY:-/etc/ega/pg.key}
PG_CA=${PG_CA:-/etc/ega/CA.cert}
PG_VERIFY_PEER=${PG_VERIFY_PEER:-0}

# used to create initial postgres directories and if run as root, ensure ownership to the "postgres" user
function create_db_directories {
    local user; user="$(id -u)"

    mkdir -p "$PGDATA"
    chmod 700 "$PGDATA"
    
    # Create the transaction log directory before initdb is run so the directory is owned by the correct user
    if [ -n "$POSTGRES_INITDB_WALDIR" ]; then
	mkdir -p "$POSTGRES_INITDB_WALDIR"
	if [ "$user" = '0' ]; then
	    find "$POSTGRES_INITDB_WALDIR" \! -user postgres -exec chown postgres '{}' +
	fi
	chmod 700 "$POSTGRES_INITDB_WALDIR"
    fi

    # allow the container to be started with `--user`
    if [ "$user" = '0' ]; then
	find "$PGDATA" \! -user postgres -exec chown postgres '{}' +
    fi
}


function handle_certs {

    if [ ! -e "${PG_SERVER_CERT}" ] || [ ! -e "${PG_SERVER_KEY}" ]; then
	# Generating the SSL certificate + key
	openssl req -x509 -newkey rsa:2048 \
		-keyout "${PG_SERVER_KEY}" -nodes \
		-out "${PG_SERVER_CERT}" -sha256 \
		-days 1000 -subj ${SSL_SUBJ}
    else
	# Otherwise use the injected ones.
	echo "Using the injected certificate/privatekey pair" 
    fi
    # Fixing the ownership and permissions
    cp "${PG_SERVER_KEY}" "${PG_SERVER_KEY}.lega"
    PG_SERVER_KEY=${PG_SERVER_KEY}.lega
    cp "${PG_SERVER_CERT}" "${PG_SERVER_CERT}.lega"
    PG_SERVER_CERT=${PG_SERVER_CERT}.lega
    chown postgres:postgres "${PG_SERVER_KEY}" "${PG_SERVER_CERT}"
    chmod 600 "${PG_SERVER_KEY}"

}


function create_pg_hba {

    # Securing the access
    #   - Kill 'trust' for local connections
    #   - Requiring password authentication for all, in case someone logs onto that machine
    #   - Using scram-sha-256 is stronger than md5
    #   - Enforcing SSL communication
    cat > $PGDATA/pg_hba.conf <<EOF
# TYPE   DATABASE   USER      ADDRESS        METHOD
local  	 all  	    all	      		     scram-sha-256
hostssl  all 	    all       127.0.0.1/32   scram-sha-256
hostssl  all  	    all       ::1/128        scram-sha-256
# Note: For the moment, not very network-separated :-p
hostssl  all  	    all       all            scram-sha-256   clientcert=${PG_VERIFY_PEER}
EOF
}

# Telling the conf file to use the certificates
# Must be called _after_ initdb, because it creates $PGDATA/pg.conf
# and initdb expects $PGDATA to be empty
function create_pg_conf {

    echo
    echo 'PostgreSQL setting paths to TLS certificates.'
    echo

    # We use /etc/ega/pg.conf.default as default and copy it to $PGDATA/pg.conf
    # /etc/ega/pg.conf.default is part of the image already:
    # See https://github.com/EGA-archive/LocalEGA-db/blob/master/pg.conf
    # And https://github.com/EGA-archive/LocalEGA-db/blob/master/Dockerfile#L27
    cp /etc/ega/pg.conf.default $PGDATA/pg.conf

    # Deleting first. `sed` exists in the image
    sed -i '/ssl_cert_file = /d' $PGDATA/pg.conf
    sed -i '/ssl_key_file = /d' $PGDATA/pg.conf
    sed -i '/ssl_ca_file = /d' $PGDATA/pg.conf

    # Adding the values
    cat >> $PGDATA/pg.conf <<EOF
ssl_cert_file = '${PG_SERVER_CERT}'
ssl_key_file = '${PG_SERVER_KEY}'
EOF

    if [ "${PG_VERIFY_PEER}" == "1" ] && [ -e "${PG_CA}" ]; then
	echo "ssl_ca_file = '${PG_CA}'" >> $PGDATA/pg.conf
    fi
}


# Convenient alias
function process_sql {
    psql -v ON_ERROR_STOP=1 --username postgres --no-password "$@"
}

function docker_process_init_files {
    local f
    for f; do
	case "$f" in
	    *.sh)
		# https://github.com/docker-library/postgres/issues/450#issuecomment-393167936
		# https://github.com/docker-library/postgres/pull/452
		if [ -x "$f" ]; then
		    echo "$0: running $f"
		    "$f"
		else
		    echo "$0: sourcing $f"
		    . "$f"
		fi
		;;
	    *.sql)    echo "$0: running $f"; process_sql --dbname lega -f "$f"; echo ;;
	    *.sql.gz) echo "$0: running $f"; gunzip -c "$f" | process_sql --dbname lega; echo ;;
	    *)        echo "$0: ignoring $f" ;;
	esac
    done
}

# initialize empty PGDATA directory with new database via 'initdb'
# arguments to `initdb` can be passed via POSTGRES_INITDB_ARGS or as arguments to this function
# `initdb` automatically creates the "postgres", "template0", and "template1" dbnames
function do_initdb {

    [[ -z "${DB_PASSWORD}" ]] && echo 'Environment DB_PASSWORD is empty' 1>&2 && exit 1

    if [ -n "$POSTGRES_INITDB_WALDIR" ]; then
	set -- --waldir "$POSTGRES_INITDB_WALDIR" "$@"
    fi

    eval 'initdb --username=postgres '"$POSTGRES_INITDB_ARGS"' "$@"' # no password: no authentication for postgres user

    # Allow "trust" authentication for local connections, during setup
    cat > $PGDATA/pg_hba.conf <<EOF
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF

    # Internal start of the server for setup via 'psql'
    # Note: does not listen on external TCP/IP and waits until start finishes
    # (PGUSER: postgres)
    pg_ctl -D "$PGDATA" -o "-c listen_addresses='' -c password_encryption=scram-sha-256" -w start

    # Create lega database
    process_sql --dbname postgres <<-'EOSQL'
SET TIME ZONE 'UTC';
CREATE DATABASE lega;
EOSQL

    # Run sql commands
    process_sql --dbname lega -f /etc/ega/db.sql

    # Extra ones from /docker-entrypoint-initdb.d
    # Note: added to the `lega` database
    docker_process_init_files /docker-entrypoint-initdb.d/*

    # Set password for lega_in and lega_out users
    process_sql --dbname lega <<EOSQL
ALTER USER lega WITH PASSWORD '${DB_PASSWORD}';
EOSQL

    # Stop the server (PGUSER: postgres)
    pg_ctl -D "$PGDATA" -m fast -w stop

}


#######################################

echo
echo 'PostgreSQL starting up.'
echo
PG_COLOR=always

create_db_directories

if [ "$(id -u)" = '0' ]; then
    handle_certs
    # then restart script as postgres user
    exec su-exec postgres "$BASH_SOURCE" "$@"
fi

# look specifically for PG_VERSION, as it is expected in the DB dir
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    # Do initilization (as postgres user)
    do_initdb
else
    echo 'PostgreSQL Database directory already setup'
fi

unset DB_PASSWORD

# always re-create the pg_hba.conf and pg.conf
create_pg_conf
create_pg_hba

echo
echo 'PostgreSQL init process complete; ready for start up.'
echo

# Finally, run, using the new pg.conf
exec postgres -c config_file=$PGDATA/pg.conf
