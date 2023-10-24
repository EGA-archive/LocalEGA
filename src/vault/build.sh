#!/usr/bin/env bash

set -Eeo pipefail

[[ -z "${POSTGRES_PASSWORD}" ]] && echo 'Environment variable POSTGRES_PASSWORD is empty' && exit 1
[[ -z "${POSTGRES_DB}" ]] && echo 'Environment variable POSTGRES_DB is empty' && exit 1
[[ -z "${PGDATA}" ]] && echo 'Environment variable PGDATA is empty' && exit 1
[[ ! -d "$PGDATA" ]] && echo '$PGDATA is not a directory' && exit 1

if ! getent passwd postgres &> /dev/null; then
    echo "The running user postgres is not found in the image" 
    exit 1
fi

# look specifically for PG_VERSION, as it is expected in the DB dir
if [ -s "$PGDATA/PG_VERSION" ]; then
    echo
    echo 'PostgreSQL Database directory appears to contain a database'
    echo 'Remove it first'
    echo
    exit 1
fi

# Create the directory with right ownership and permissions, as root
if [ "$(id -u)" = '0' ]; then

    chmod 700 "$PGDATA" || : # ignore failure
    chown -R postgres "$PGDATA" # not the group

    mkdir -p /var/run/postgresql || :
    chmod 775 /var/run/postgresql || :
    chown postgres "$PGDATA"

    # Restart as the postgres user
    exec gosu postgres "$BASH_SOURCE" "$@"
fi

#
# Initialize the database cluster
#
# See https://www.postgresql.org/docs/13/app-initdb.html
#

export PG_COLOR=auto

# Run the init command
# We use postgres as the superuser
# --waldir=directory
# --wal-segsize=size
echo "Initialization $PGDATA as $(id)"
initdb --username=postgres \
       --pwfile=<(echo "$POSTGRES_PASSWORD") \
       --auth-host=scram-sha-256 \
       -D "$PGDATA"

# internal start of server in order to allow setup using psql client
# does not listen on external TCP/IP and waits until start finishes
# Note: the $PGDATA/pg_hba.conf sets all connections to trust
echo "Starting the server internally"
PGUSER=postgres \
      pg_ctl -D "$PGDATA" \
             -o "-c listen_addresses='localhost' -c password_encryption=scram-sha-256 -p 5432" \
	     -o "-c crypt4gh.master_seckey=fake -c shared_preload_libraries='pg_crypt4gh'" \
	     -w start

# Stop the server when exiting and receiving an interrupt
function stop_server {
    echo "Stopping the server"
    PGUSER=postgres pg_ctl -D "$PGDATA" -m fast -w stop
}
trap stop_server EXIT SIGINT

echo "Create the database $POSTGRES_DB"
psql -v ON_ERROR_STOP=1 --username postgres --no-password --dbname postgres --set db="$POSTGRES_DB" <<-'EOSQL'
    CREATE DATABASE :"db" ;
EOSQL

if [ -d /ega/initdb.d/ ]; then
    echo "Load the SQL files"
    function process_sql {
	psql -v ON_ERROR_STOP=1 --username postgres --no-password --dbname "$POSTGRES_DB" $@
    }
    pushd /ega/initdb.d/
    for f in *; do
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
	    *.sql)    echo "$0: running $f"; process_sql -f "$f"; echo ;;
	    *.sql.gz) echo "$0: running $f"; gunzip -c "$f" | process_sql; echo ;;
	    *.sql.xz) echo "$0: running $f"; xzcat "$f" | process_sql; echo ;;
	    *)        echo "$0: ignoring $f" ;;
	esac
	echo
    done
fi

echo "Deleting key files"
rm -f $PGDATA/pg_hba.conf
rm -f $PGDATA/postgresql.conf
rm -f $PGDATA/postmaster.opts
    
echo 
echo 'PostgreSQL DB initialization complete.'
echo

# Note: Let the trap will stop the server
