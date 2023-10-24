GRANT USAGE ON SCHEMA fs TO lega;
GRANT EXECUTE ON FUNCTION fs.trigger_nss_users() TO lega;
GRANT EXECUTE ON FUNCTION fs.make_nss_users() TO lega;
GRANT EXECUTE ON FUNCTION fs.trigger_nss_passwords() TO lega;
GRANT EXECUTE ON FUNCTION fs.make_nss_passwords() TO lega;
GRANT EXECUTE ON FUNCTION fs.make_nss_groups() TO lega;
GRANT EXECUTE ON FUNCTION fs.trigger_authorized_keys() TO lega;
GRANT EXECUTE ON FUNCTION fs.make_authorized_keys TO lega;

-- GRANT pg_write_server_files TO lega;

