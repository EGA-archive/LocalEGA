#!/usr/bin/env bash
set -Eeo pipefail
# TODO swap to -Eeuo pipefail above (after handling all potentially-unset variables)

if [ "$(id -u)" = '0' ]; then
    # When root
    mkdir -p "$PGDATA"
    chown -R postgres "$PGDATA"
    chmod 700 "$PGDATA"
    mkdir -p /var/run/postgresql
    chown -R postgres /var/run/postgresql
    chmod 775 /var/run/postgresql

    mkdir -p /etc/ega
    chgrp postgres /etc/ega
    chmod 770 /etc/ega

    # Run again as 'postgres'
    exec gosu postgres "$BASH_SOURCE" "$@"
fi

# If already initiliazed, then run
if [ -s "$PGDATA/PG_VERSION" ]; then
    # Remove the secrets
    #rm -f /run/secrets/db_lega_in
    #rm -f /run/secrets/db_lega_out
    # And..... cue music
    exec postgres -c config_file=/etc/ega/pg.conf
fi

# Don't init if secrets not defined
[[ ! -s "/run/secrets/db_lega_in" ]] && echo 'DB Lega-IN secret missing' 1>&2 && exit 1
[[ ! -s "/run/secrets/db_lega_out" ]] && echo 'DB Lega-OUT secret missing' 1>&2 && exit 1

# Generating the SSL certificate + key
openssl req -x509 -newkey rsa:2048 \
	    -keyout /etc/ega/pg.key -nodes \
	    -out /etc/ega/pg.cert -sha256 \
	    -days 1000 -subj ${SSL_SUBJ}
chown postgres:postgres /etc/ega/pg.{key,cert}
chmod 600 /etc/ega/pg.key

# Otherwise, do initilization (as postgres user)
initdb --username=postgres # no password: no authentication for postgres user

# Allow "trust" authentication for local connections, during setup
cat > $PGDATA/pg_hba.conf <<EOF
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF

# Internal start of the server for setup via 'psql'
# Note: does not listen on external TCP/IP and waits until start finishes
pg_ctl -D "$PGDATA" -o "--listen_addresses='' --password_encryption=scram-sha-256" -w start

# Create lega database
psql -v ON_ERROR_STOP=1 --username postgres --no-password --dbname postgres <<-'EOSQL'
     SET TIME ZONE 'UTC';
     CREATE DATABASE lega;
EOSQL

# Run sql commands (in order!)
DB_FILES=(/docker-entrypoint-initdb.d/main.sql
	  /docker-entrypoint-initdb.d/download.sql
	  /docker-entrypoint-initdb.d/qc.sql
	  /docker-entrypoint-initdb.d/grants.sql)

for f in ${DB_FILES[@]}; do # in order
    echo "$0: running $f";
    echo
    psql -v ON_ERROR_STOP=1 --username postgres --no-password --dbname lega -f $f;
    echo
done

# Set password for lega_in and lega_out users
echo "Password for lega-in:  -----$(</run/secrets/db_lega_in)-----"
echo "Password for lega-out: -----$(</run/secrets/db_lega_out)-----"

# Set password for lega_in and lega_out users
psql -v ON_ERROR_STOP=1 --username postgres --no-password --dbname lega <<EOSQL
     ALTER USER lega_in WITH PASSWORD '$(</run/secrets/db_lega_in)';
     ALTER USER lega_out WITH PASSWORD '$(</run/secrets/db_lega_out)';
EOSQL


# Stop the server
pg_ctl -D "$PGDATA" -m fast -w stop

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
hostssl  all  	    all       all            scram-sha-256
EOF


echo
echo 'PostgreSQL init process complete; ready for start up.'
echo

# Remove the secrets
#rm -f /run/secrets/db_lega_in
#rm -f /run/secrets/db_lega_out
# And..... cue music
exec postgres -c config_file=/etc/ega/pg.conf
