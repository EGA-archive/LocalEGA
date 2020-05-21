-- \connect lega

-- NOTE: since we only have one user: lega_in
-- we grant it access directly inside of setting up roles
CREATE USER lega;

-- Set up rights access for local_ega schema
GRANT USAGE ON SCHEMA local_ega TO lega;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA local_ega TO lega; -- Read/Write access on local_ega.* for lega
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA local_ega TO lega; -- Don't forget the sequences
