psql -v ON_ERROR_STOP=1 --username postgres <<-EOSQL
ALTER USER "$POSTGRES_USER" WITH SUPERUSER '${db_password}';
EOSQL
psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres -f /tmp/db.sql
