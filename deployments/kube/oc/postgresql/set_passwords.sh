#!/bin/bash

if [[ ",$postinitdb_actions," = *,simple_db,* ]]; then
psql --command "ALTER USER \"${POSTGRESQL_USER}\" WITH ENCRYPTED PASSWORD '${POSTGRESQL_PASSWORD}';"
fi

if [ -v POSTGRESQL_MASTER_USER ]; then
psql --command "ALTER USER \"${POSTGRESQL_MASTER_USER}\" WITH REPLICATION;"
psql --command "ALTER USER \"${POSTGRESQL_MASTER_USER}\" WITH ENCRYPTED PASSWORD '${POSTGRESQL_MASTER_PASSWORD}';"
fi

if [ -v POSTGRESQL_ADMIN_PASSWORD ]; then
psql --command "ALTER USER \"postgres\" WITH ENCRYPTED PASSWORD '${POSTGRESQL_ADMIN_PASSWORD}';"
fi

psql -U postgres -d $POSTGRESQL_DATABASE -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
psql -U $POSTGRESQL_USER -d $POSTGRESQL_DATABASE -c "\i /usr/share/container-scripts/db.sql"
