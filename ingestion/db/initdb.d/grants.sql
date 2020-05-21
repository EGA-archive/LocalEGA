-- \connect lega

-- NOTE: since we only have one user: lega_in
-- we grant it access directly inside of setting up roles
CREATE USER lega_in;

-- Set up rights access for local_ega schema
GRANT USAGE ON SCHEMA local_ega TO lega_in;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA local_ega TO lega_in; -- Read/Write access on local_ega.* for lega_in
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA local_ega TO lega_in; -- Don't forget the sequences
