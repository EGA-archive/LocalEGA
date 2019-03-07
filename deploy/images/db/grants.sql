-- \connect lega

-- CREATE ROLE lega_reader NOINHERIT;
-- CREATE ROLE lega_writer NOINHERIT;
-- CREATE USER lega_in WITH ROLE lega_reader
--                     WITH ROLE lega_writer;
-- CREATE USER lega_out WITH ROLE lega_reader;


-- NOTE: since we only have 2 users: lega_in, lega_out
-- we grant them access directly inside of setting up roles
CREATE USER lega_in;
CREATE USER lega_out;

-- Set up rights access for local_ega schema
GRANT USAGE ON SCHEMA local_ega TO lega_in, lega_out;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA local_ega TO lega_in; -- Read/Write access on local_ega.* for lega_in
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA local_ega TO lega_in; -- Don't forget the sequences
GRANT SELECT ON local_ega.archive_files  TO lega_out;                    -- Read-Only access for lega_out

-- Set up rights access for audit schema
GRANT USAGE ON SCHEMA local_ega_download TO lega_out;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA local_ega_download TO lega_out; -- Read/Write on audit.* for lega_out
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA local_ega_download TO lega_out; -- Don't forget the sequences

-- Set up rights access for local_ega_ebi schema
GRANT USAGE ON SCHEMA local_ega_ebi TO lega_out;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA local_ega_ebi TO lega_out;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA local_ega_ebi TO lega_out;
