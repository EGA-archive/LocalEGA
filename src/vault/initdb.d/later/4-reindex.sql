
-- #####################
-- Users
-- #####################

REINDEX INDEX CONCURRENTLY username_idx;
REINDEX INDEX CONCURRENTLY user_id_idx;
REINDEX INDEX CONCURRENTLY idx_user_id_user_key_table;
REINDEX INDEX CONCURRENTLY idx_user_id_user_password_table;

-- #####################
-- Datasets 
-- #####################

REINDEX INDEX CONCURRENTLY idx_dataset_id_include_enabled_stable_id;
REINDEX INDEX CONCURRENTLY ega_stable_id_idx;

-- #####################
-- Files
-- #####################

REINDEX INDEX CONCURRENTLY idx_file_id_include_enabled_stable_id;
REINDEX INDEX CONCURRENTLY idx_private_file_id;
REINDEX INDEX CONCURRENTLY dft_idx;
