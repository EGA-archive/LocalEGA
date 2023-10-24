-- ###################################################
-- Grant permissions to the distribution user
-- ###################################################

GRANT USAGE ON SCHEMA public TO distribution;
GRANT SELECT ON public.dataset_table to distribution;
GRANT SELECT ON public.dataset_file_table TO distribution;
GRANT SELECT ON public.file_table TO distribution;
GRANT SELECT ON public.user_table to distribution;
GRANT SELECT ON public.user_key_table to distribution;
GRANT SELECT ON public.header_keys to distribution;

GRANT USAGE ON SCHEMA private TO distribution;
GRANT SELECT ON private.file_table TO distribution;
--GRANT SELECT ON private.username_file_header to distribution;
GRANT SELECT ON private.dataset_permission_table to distribution;

GRANT USAGE ON SCHEMA fs TO distribution;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA fs TO distribution;

GRANT USAGE     ON SCHEMA crypt4gh                                      TO distribution;
GRANT EXECUTE   ON FUNCTION crypt4gh.header_reencrypt(bytea,bytea)      TO distribution;
GRANT EXECUTE   ON FUNCTION crypt4gh.header_reencrypt(bytea,bytea[])    TO distribution;

-- LEGA user
GRANT USAGE 				ON SCHEMA public 			TO lega;
GRANT USAGE				ON SEQUENCE user_table_id_seq		TO lega;
GRANT SELECT,INSERT,UPDATE,DELETE	ON TABLE public.user_table		TO lega;
GRANT USAGE				ON SEQUENCE user_key_table_id_seq	TO lega;
GRANT SELECT,INSERT,DELETE 		ON TABLE public.user_key_table 		TO lega;
GRANT SELECT,INSERT,UPDATE,DELETE 	ON TABLE public.file_table 		TO lega;

GRANT SELECT,INSERT,UPDATE,DELETE	ON TABLE public.dac_table 		TO lega; -- delete, too?
GRANT SELECT,INSERT,UPDATE 		ON TABLE public.dataset_table 		TO lega; -- delete, too?
GRANT SELECT,INSERT,UPDATE,DELETE 	ON TABLE public.dac_dataset_table 	TO lega;
GRANT SELECT,INSERT,UPDATE,DELETE	ON TABLE public.dac_user_table 		TO lega;
GRANT SELECT,INSERT,DELETE		ON TABLE public.dataset_file_table 	TO lega;

GRANT SELECT				ON TABLE public.requesters		TO lega;
GRANT SELECT				ON TABLE public.ssh_keys		TO lega;

GRANT USAGE 				ON SCHEMA private 			TO lega;
GRANT SELECT,INSERT,UPDATE,DELETE 	ON TABLE private.file_table 		TO lega;
GRANT USAGE                             ON SEQUENCE private.dataset_permission_table_id_seq TO lega;
GRANT SELECT,INSERT,UPDATE,DELETE	ON TABLE private.dataset_permission_table	TO lega;
GRANT SELECT,INSERT,UPDATE,DELETE	ON TABLE private.user_password_table		TO lega;

GRANT EXECUTE ON FUNCTION public.extract_name(text) 				TO lega;
GRANT EXECUTE ON FUNCTION public.upsert_file 					TO lega;
GRANT EXECUTE ON FUNCTION public.process_dac_dataset_message(jsonb) 		TO lega;
GRANT EXECUTE ON FUNCTION public.process_mapping_message(jsonb) 		TO lega;
GRANT EXECUTE ON FUNCTION public.process_release_message 			TO lega;
GRANT EXECUTE ON FUNCTION public.process_deprecated_message 			TO lega;
GRANT EXECUTE ON FUNCTION public.process_permission_message 			TO lega;
GRANT EXECUTE ON FUNCTION public.process_deleted_permission_message 		TO lega;
GRANT EXECUTE ON FUNCTION public.process_user_password_message             	TO lega;
GRANT EXECUTE ON FUNCTION public.process_user_keys_message             		TO lega;
GRANT EXECUTE ON FUNCTION public.process_user_contact_message             	TO lega;

GRANT USAGE	ON SCHEMA crypt4gh 					TO lega;
GRANT EXECUTE 	ON FUNCTION crypt4gh.parse_pubkey 			TO lega;

-- TODO
-- #####################################################
-- Grant permissions to the permission user
-- (e.g. listing requests, granting/denying requests)
-- #####################################################

GRANT USAGE 			ON SCHEMA public 					TO permission;
GRANT SELECT 			ON public.user_table 					TO permission;
GRANT SELECT 			ON public.dac_table 					TO permission;
GRANT SELECT 			ON public.dac_dataset_table 				TO permission;
GRANT SELECT 			ON public.dataset_table 				TO permission;

GRANT USAGE 			ON SCHEMA request 					TO permission;
GRANT SELECT			ON ALL TABLES IN SCHEMA request				TO permission;

GRANT USAGE                     ON SEQUENCE request.permission_action_table_id_seq     	TO permission;
GRANT SELECT,INSERT,UPDATE 	ON request.permission_action_table 			TO permission;

GRANT EXECUTE 			ON ALL FUNCTIONS IN SCHEMA request 			TO permission;

GRANT USAGE 			ON SCHEMA private 					TO permission;
GRANT USAGE			ON SEQUENCE private.dataset_permission_table_id_seq	TO permission;
GRANT SELECT,INSERT,DELETE 	ON private.dataset_permission_table 			TO permission;
--GRANT SELECT 			ON private.permission 					TO permission;

