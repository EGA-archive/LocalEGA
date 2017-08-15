psql -v ON_ERROR_STOP=1 -U postgres <<-EOSQL
ALTER USER postgres WITH password '${db_password}';
EOSQL
psql -v ON_ERROR_STOP=1 -U postgres -f /tmp/db.sql
