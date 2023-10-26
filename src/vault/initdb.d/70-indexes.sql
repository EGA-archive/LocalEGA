
-- #####################
-- Users
-- #####################


CREATE INDEX username_idx ON public.user_table USING btree (id, username);

CREATE INDEX user_id_idx ON private.dataset_permission_table USING btree (user_id, dataset_stable_id);


CREATE INDEX idx_user_id_user_key_table
ON public.user_key_table
USING btree (user_id ASC NULLS LAST)
;

CREATE INDEX idx_user_id_user_password_table
ON private.user_password_table
USING btree (user_id ASC NULLS LAST)
;


-- #####################
-- Files
-- #####################

-- CREATE INDEX idx_file_id_include_enabled_stable_id
-- ON public.dataset_file_table
-- USING btree (node_name, id ASC NULLS LAST)
-- INCLUDE (dataset_stable_id)
-- ;

CREATE INDEX idx_file_stable_id_include_id
ON public.dataset_file_table
USING btree (stable_id ASC NULLS LAST)
INCLUDE (id)
;

CREATE INDEX idx_file_id_include_enabled_stable_id
ON public.dataset_file_table
USING btree (dataset_stable_id ASC NULLS LAST)
INCLUDE (node_name, id)
;

CREATE INDEX idx_private_file_id
ON private.dataset_file_table
USING btree (id ASC NULLS LAST)
INCLUDE (node_name)
;



-- when we do the translation from dataset to file stables ids,
-- this will be fast and for distribution, it will find the ids fast to lookup the info it needs
CREATE INDEX dft_idx ON public.dataset_file_table USING btree(dataset_stable_id, stable_id) INCLUDE (id);
