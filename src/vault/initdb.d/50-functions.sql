-- TODO: Create functions
-- 1. Insert,update or delete DACs, datasets? & dac-dataset links (Rabbit message)
-- 2. Inserting requests
-- 3. Granting/denying requests: insert into private.permission_table (granting) + public.permission_action_table (granting or denying)

CREATE OR REPLACE FUNCTION public.extract_name(_original_filepath text)
RETURNS text
LANGUAGE plpgsql
AS $_$
DECLARE
        _result text;
BEGIN

	--delete extensions
	select regexp_replace(_original_filepath,'\.c4gh$', '') INTO _result;

	--delete possible beginnings
	select replace(_result, '/ega/inbox/', '') INTO _result;

	-- remove leading /
	select trim(leading '/' from _result) INTO _result;

	--replace / with _
	select replace(_result, '/', '_') INTO _result;

	return _result;
END
$_$;

CREATE OR REPLACE FUNCTION public.upsert_file(
        _inbox_path text,
        _filesize bigint, -- encrypted payload filesize
        _header bytea,
        _payload_sha256_checksum text,
        _decrypted_sha256_checksum text,
        _accession_id text,
        _relative_path text
)
RETURNS void
LANGUAGE plpgsql
AS $_$
BEGIN
        -- TODO: Check parameters

        WITH ins_file AS (
                INSERT INTO public.file_table AS t(stable_id, filesize, display_name)
                VALUES(_accession_id,
		       _filesize + octet_length(_header), -- we add "this" header size (once re-encrypted it might be bigger)
		       public.extract_name(_inbox_path))
                ON CONFLICT ON CONSTRAINT file_table_pkey
                DO UPDATE
                SET filesize=EXCLUDED.filesize,
                    display_name=EXCLUDED.display_name
                RETURNING t.stable_id
        )
        INSERT INTO private.file_table(stable_id, relative_path, header, payload_size, payload_checksum, decrypted_checksum)
        SELECT stable_id, _relative_path, _header, _filesize, _payload_sha256_checksum, _decrypted_sha256_checksum
        FROM ins_file
        ON CONFLICT DO NOTHING;

END
$_$;


CREATE OR REPLACE FUNCTION public.process_mapping_message(_json_message jsonb)
    RETURNS bigint
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	_rows_inserted bigint;
BEGIN
	WITH metadata_data(metadata_json) AS (
		SELECT (_json_message)

	), metadata_rows AS (
		SELECT --metadata_json->>'type' AS type, 
			metadata_json->>'dataset_id' AS dataset_accession_id,
			jsonb_array_elements_text(metadata_json->'accession_ids') AS file_accession_id
		FROM metadata_data s

	), ins_dataset AS (
		INSERT INTO public.dataset_table AS dft (stable_id)
		SELECT s.dataset_accession_id
		FROM metadata_rows s
		ON CONFLICT ON CONSTRAINT dataset_table_pkey
		DO NOTHING
	), find_links AS (
		SELECT dft.dataset_stable_id, dft.file_stable_id
		FROM public.dataset_file_table dft
		INNER JOIN metadata_rows s ON s.dataset_accession_id=dft.dataset_stable_id
		LEFT JOIN metadata_rows s2 ON s2.dataset_accession_id=dft.dataset_stable_id
						AND s2.file_accession_id=dft.file_stable_id
		WHERE s2.file_accession_id IS NULL -- this file is no longer in the list
	), del_removed_links AS (
		DELETE FROM public.dataset_file_table dft
		USING find_links
		WHERE dft.dataset_stable_id=find_links.dataset_stable_id
			AND dft.file_stable_id=find_links.file_stable_id
	), insrt AS (
		INSERT INTO public.dataset_file_table AS dft (dataset_stable_id, file_stable_id)
		SELECT s.dataset_accession_id, s.file_accession_id
		FROM metadata_rows s
		LEFT JOIN public.dataset_file_table already ON s.dataset_accession_id=already.dataset_stable_id
								AND s.file_accession_id=already.file_stable_id
		WHERE already.file_stable_id IS NULL -- file is not present in the table
		RETURNING dft.file_stable_id
	)
	SELECT count(*) INTO _rows_inserted
	FROM insrt;

	RETURN _rows_inserted;

END
$BODY$;


CREATE OR REPLACE FUNCTION public.process_release_message(_json_message jsonb)
RETURNS bigint
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	_rows bigint;
BEGIN
	WITH metadata_data(metadata_json) AS (
			SELECT (_json_message)
	), metadata_rows AS (
			SELECT metadata_json->>'dataset_id' AS dataset_accession_id
			FROM metadata_data s
	), upd AS (
		UPDATE public.dataset_table AS t
		SET is_released=true
		FROM metadata_rows
		WHERE t.stable_id=dataset_accession_id
		RETURNING t.stable_id
	)
	SELECT count(*) INTO _rows
	FROM upd;

	RETURN _rows;
END
$BODY$;

CREATE OR REPLACE FUNCTION public.process_deprecated_message(_json_message jsonb)
RETURNS bigint
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	_rows bigint;
BEGIN
	WITH metadata_data(metadata_json) AS (
			SELECT (_json_message)
	), metadata_rows AS (
			SELECT metadata_json->>'dataset_id' AS dataset_accession_id
			FROM metadata_data s
	), upd AS (
		UPDATE public.dataset_table AS t
		SET is_deprecated=true,
			is_released=false
		FROM metadata_rows
		WHERE t.stable_id=dataset_accession_id
		RETURNING t.stable_id
	)
	SELECT count(*) INTO _rows
	FROM upd;

	RETURN _rows;
END
$BODY$;


CREATE OR REPLACE FUNCTION public.process_permission_message(_json_message jsonb)
    RETURNS bigint
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
	_stable_id text;
	_user jsonb;
	_username text;
	_user_id bigint;
BEGIN
	_stable_id = _json_message->>'dataset_id';
	IF _stable_id IS NULL THEN
		RAISE EXCEPTION 'dataset id is required';
	END IF;

	_user = _json_message->'user';
	IF _user IS NULL THEN
		RAISE EXCEPTION 'user is required';
	END IF;

	_username = _user->>'username';

	RAISE NOTICE '_username= %', _username;

	-----------------
	-- Upsert user --
	-----------------
	-- We not use ON CONFLICT DO UPDATE here to not increment the sequence
	-- every time the user already exists (we will receive many permissions for the same user)

	UPDATE public.user_table t
	SET full_name=_user->>'full_name',
		email=_user->>'email',
		institution=_user->>'institution',
		country=_user->>'country'
	WHERE t.username = _username
	RETURNING t.id INTO _user_id;

	IF _user_id IS NULL THEN
		INSERT INTO public.user_table AS t (username, group_id, full_name, email, institution, country)
		SELECT _username, 20000, _user->>'full_name', _user->>'email', _user->>'institution', _user->>'country'
		RETURNING t.id INTO _user_id;
	END IF;

	---------------------
	-- Upsert password --
	---------------------
	INSERT INTO private.user_password_table (user_id, password_hash)
	SELECT _user_id,  _user->>'password_hash'
	ON CONFLICT ON CONSTRAINT user_password_table_pkey
	DO UPDATE
	SET password_hash=EXCLUDED.password_hash
	;

	-----------------
	-- Insert keys --
	-----------------
	-- 1st) Delete existing keys
	DELETE FROM public.user_key_table
	WHERE user_id=_user_id;

	-- 2n) Insert keys
	INSERT INTO public.user_key_table (user_id, key, type)
	SELECT _user_id, _val->>'key', (_val->>'type')::public.key_type
	FROM jsonb_array_elements(_user->'keys') _val;

	-----------------------
	-- Upsert permission --
	-----------------------
	UPDATE private.dataset_permission_table
	SET expires_at=(_json_message->>'expires_at')::timestamp with time zone,
		edited_at=(_json_message->>'edited_at')::timestamp with time zone
	WHERE dataset_stable_id=_stable_id AND user_id=_user_id;

	IF NOT FOUND THEN
		INSERT INTO private.dataset_permission_table (dataset_stable_id, user_id, expires_at, created_at, edited_at)
		SELECT _stable_id,
		_user_id,
		(_json_message->>'expires_at')::timestamp with time zone,
		(_json_message->>'created_at')::timestamp with time zone,
		(_json_message->>'edited_at')::timestamp with time zone;
	END IF;

	RETURN 1;
END
$BODY$;



CREATE OR REPLACE FUNCTION public.process_deleted_permission_message(_json_message jsonb)
    RETURNS bigint
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	_stable_id text;
	_user text;
BEGIN
	_stable_id = _json_message->>'dataset_id';
	IF _stable_id IS NULL THEN
		RAISE EXCEPTION 'dataset id is required';
	END IF;

	_user = _json_message->>'user';
	IF _user IS NULL THEN
		RAISE EXCEPTION 'user is required';
	END IF;

	-----------------------
	-- Delete permission --
	-----------------------
	DELETE FROM private.dataset_permission_table dpt
	USING public.user_table ut
	WHERE dpt.user_id=ut.id AND ut.username=_user AND dpt.dataset_stable_id=_stable_id;

	RETURN 1;
END
$BODY$;

CREATE OR REPLACE FUNCTION public.process_user_password_message(_json_message jsonb)
    RETURNS bigint
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	_username text;
	_password_hash text;
BEGIN
	_username = _json_message->>'user';
	IF _username IS NULL THEN
		RAISE EXCEPTION 'user is required';
	END IF;

	_password_hash = _json_message->>'password_hash';
	IF _password_hash IS NULL THEN
		RAISE EXCEPTION 'password hash is required';
	END IF;

	---------------------
	-- Update password --
	---------------------
	UPDATE private.user_password_table upt
	SET password_hash=_password_hash
	FROM user_table ut
	WHERE upt.user_id=ut.id AND ut.username=_username;

	RETURN 1;
END
$BODY$;


CREATE OR REPLACE FUNCTION public.process_user_keys_message(_json_message jsonb)
    RETURNS bigint
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	_username text;
	_keys jsonb;
	_user_id bigint;
BEGIN
	_username = _json_message->>'user';
	IF _username IS NULL THEN
		RAISE EXCEPTION 'user is required';
	END IF;

	_keys = _json_message->>'keys';
	IF _keys IS NULL THEN
		RAISE EXCEPTION 'keys is required';
	END IF;

	SELECT ut.id INTO _user_id
	FROM public.user_table ut
	WHERE ut.username=_username;

	IF _user_id IS NULL THEN
		RAISE EXCEPTION 'User not found';
	END IF;

    -----------------
    -- Insert keys --
    -----------------
    -- 1st) Delete existing keys
    DELETE FROM public.user_key_table
    WHERE user_id=_user_id;

    -- 2n) Insert keys
    INSERT INTO public.user_key_table (user_id, key, type)
    SELECT _user_id, _val->>'key', (_val->>'type')::public.key_type
    FROM jsonb_array_elements(_keys) _val;

	RETURN 1;
END
$BODY$;


CREATE OR REPLACE FUNCTION public.process_user_contact_message(_json_message jsonb)
    RETURNS bigint
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
	_username text;
	_user_id bigint;
BEGIN	
	_username = _json_message->>'user';
	IF _username IS NULL THEN 
		RAISE EXCEPTION 'username is required';
	END IF;
	
    -----------------
    -- Update user --
    -----------------
    UPDATE public.user_table t
    SET full_name=_json_message->>'full_name',
            email=_json_message->>'email',
            institution=_json_message->>'institution',
            country=_json_message->>'country'
    WHERE t.username = _username
    RETURNING t.id INTO _user_id;

	IF _user_id IS NULL THEN
		RAISE EXCEPTION 'User not found';
	END IF;
	
	RETURN 1;
END
$BODY$;

CREATE OR REPLACE FUNCTION public.process_dac_dataset_message(_json_message jsonb)
RETURNS bigint
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
        _rows_inserted bigint;
BEGIN
		-- Dacs & datasets
        WITH metadata_data(metadata_json) AS (
                SELECT (_json_message)

        ), metadata_rows AS (
                SELECT --metadata_json->>'type' AS type,
                        metadata_json->>'accession_id' AS accession_id,
                        metadata_json->>'title' AS title,
						metadata_json->>'description' AS description,
                        metadata_json->'datasets' AS datasets -- jsonb
                FROM metadata_data s

        ), upsert_dac AS (
                INSERT INTO public.dac_table AS t (stable_id, title, description)
                SELECT s.accession_id, s.title, s.description
                FROM metadata_rows s
                ON CONFLICT ON CONSTRAINT dac_table_pkey
                DO UPDATE
                SET title=EXCLUDED.title,
                	description=EXCLUDED.description
                RETURNING t.stable_id

        ), upsert_datasets AS (
                INSERT INTO public.dataset_table AS t (stable_id, title, description)
                SELECT dataset->>'accession_id',
					dataset->>'title',
					dataset->>'description'
                FROM metadata_rows s
                INNER JOIN jsonb_array_elements(NULLIF(s.datasets, 'null')) t(dataset) ON TRUE
                ON CONFLICT ON CONSTRAINT dataset_table_pkey
                DO UPDATE
                SET title=EXCLUDED.title,
					description=EXCLUDED.description
                RETURNING t.stable_id

        ), find_links AS (
                SELECT upsert_dac.stable_id AS dac_stable_id,
                        upsert_datasets.stable_id AS dataset_stable_id
                FROM upsert_dac,
                        upsert_datasets

        ), del_old_links AS (
                -- If the dataset has been changed to another DAC,
                -- the old dac-dataset link must be deleted
                DELETE FROM public.dac_dataset_table ddt
                USING find_links
                WHERE ddt.dataset_stable_id=find_links.dataset_stable_id
                        AND ddt.dac_stable_id!=find_links.dac_stable_id

        ), insert_links AS (
                INSERT INTO public.dac_dataset_table AS t (dac_stable_id, dataset_stable_id)
                SELECT find_links.dac_stable_id, find_links.dataset_stable_id
                FROM find_links
                ON CONFLICT ON CONSTRAINT dac_dataset_table_pkey
                DO NOTHING
                RETURNING t.dac_stable_id

        )
        SELECT count(*) INTO _rows_inserted
        FROM insert_links
        ;

		-- Dacs & users
		WITH metadata_data(metadata_json) AS (
                SELECT (_json_message)

        ), metadata_rows AS (
                SELECT --metadata_json->>'type' AS type,
                        metadata_json->>'accession_id' AS accession_id,
						metadata_json->'users' AS users --jsonb
                FROM metadata_data s

        ), insert_users AS (
			INSERT INTO public.user_table AS t (username, group_id, full_name, email, institution, country)
			SELECT us->>'username', 20000, us->>'full_name', us->>'email', us->>'institution', us->>'country'
			FROM metadata_rows s
            INNER JOIN jsonb_array_elements(NULLIF(s.users, 'null')) t(us) ON TRUE
			ON CONFLICT ON CONSTRAINT user_table_username_key
			DO UPDATE
			SET full_name=EXCLUDED.full_name,
                email=EXCLUDED.email,
                institution=EXCLUDED.institution,
                country=EXCLUDED.country
			RETURNING t.id, t.username
		), ins_password AS (
			INSERT INTO private.user_password_table AS t (user_id, password_hash, is_enabled)
			SELECT insert_users.id, us->>'password_hash', true
			FROM metadata_rows s
			INNER JOIN jsonb_array_elements(NULLIF(s.users, 'null')) t(us) ON TRUE
			INNER JOIN insert_users ON insert_users.username=us->>'username'
			ON CONFLICT ON CONSTRAINT user_password_table_pkey
			DO UPDATE
			SET password_hash=EXCLUDED.password_hash,
				is_enabled=true

		), del_dac_users AS ( -- Remove users no longer in this DAC
			DELETE FROM public.dac_user_table t
			USING metadata_rows s, insert_users
			WHERE t.dac_stable_id=s.accession_id
				AND t.user_id!=insert_users.id
		)
		-- Insert or update users in this DAC
		INSERT INTO public.dac_user_table AS t (dac_stable_id, user_id, is_main, member_type)
		SELECT s.accession_id, insert_users.id, (us->>'is_main')::bool, (us->>'member_type')::public.member_type
		FROM metadata_rows s
		INNER JOIN jsonb_array_elements(NULLIF(s.users, 'null')) t(us) ON TRUE
		INNER JOIN insert_users ON insert_users.username=us->>'username'
		ON CONFLICT ON CONSTRAINT dac_user_table_pkey
		DO UPDATE
		SET is_main=EXCLUDED.is_main,
			member_type=EXCLUDED.member_type
		;

		---------------------
		-- CLEANUP orphans --
		---------------------

        -- Delete orphan dac-users
        WITH del_dac AS (
                SELECT dac.stable_id
                FROM public.dac_table dac
                LEFT JOIN public.dac_dataset_table dac_dat ON dac_dat.dac_stable_id=dac.stable_id
                WHERE dac_dat.dataset_stable_id IS NULL -- Find DACs not linked to any dataset
        )
		DELETE FROM public.dac_user_table t
		USING del_dac
		WHERE t.dac_stable_id=del_dac.stable_id
		;

		-- Delete orphan user data (oprhan means that they have no permissions and they are not members of any DAC)
		WITH no_perm_no_dac AS (
			SELECT us.id AS user_id
			FROM public.user_table us
			LEFT JOIN private.dataset_permission_table dpt ON dpt.user_id=us.id
			LEFT JOIN public.dac_user_table dac_us ON dac_us.user_id=us.id
			WHERE dpt.dataset_stable_id IS NULL -- user w/o permissions
				AND dac_us.dac_stable_id IS NULL -- user not a member of any DAC
		), del_passwords AS (
			DELETE FROM private.user_password_table t
			USING no_perm_no_dac p
			WHERE t.user_id=p.user_id

		)
		DELETE FROM public.user_key_table t
		USING no_perm_no_dac p
		WHERE t.user_id=p.user_id
		;

		-- Delete orphan users
        WITH no_perm_no_dac AS (
			SELECT us.id AS user_id
			FROM public.user_table us
			LEFT JOIN private.dataset_permission_table dpt ON dpt.user_id=us.id
			LEFT JOIN public.dac_user_table dac_us ON dac_us.user_id=us.id
			WHERE dpt.dataset_stable_id IS NULL -- user w/o permissions
				AND dac_us.dac_stable_id IS NULL -- user not a member of any DAC
		)
		DELETE FROM public.user_table t
		USING no_perm_no_dac p
		WHERE t.id=p.user_id
		;

		-- Delete orphan DACs
 		WITH del_dac AS (
			SELECT dac.stable_id
			FROM public.dac_table dac
			LEFT JOIN public.dac_dataset_table dac_dat ON dac_dat.dac_stable_id=dac.stable_id
			WHERE dac_dat.dataset_stable_id IS NULL -- Find DACs not linked to any dataset
        )
		DELETE FROM public.dac_table t
		USING del_dac
		WHERE t.stable_id=del_dac.stable_id
		;

        RETURN _rows_inserted;
END
$BODY$;

CREATE OR REPLACE FUNCTION public.process_dac_members_message(
	_json_message jsonb)
    RETURNS bigint
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
        _rows bigint;
BEGIN

	-- Dacs & users
	WITH metadata_data(metadata_json) AS (
                SELECT (_json_message)

        ), metadata_rows AS (
                SELECT --metadata_json->>'type' AS type,
                        metadata_json->>'accession_id' AS accession_id,
			metadata_json->'users' AS users --jsonb
                FROM metadata_data s

        ), insert_users AS (
		INSERT INTO public.user_table AS t (username, group_id, full_name, email, institution, country)
		SELECT us->>'username', 20000, us->>'full_name', us->>'email', us->>'institution', us->>'country'
		FROM metadata_rows s
		INNER JOIN jsonb_array_elements(NULLIF(s.users, 'null')) t(us) ON TRUE
		ON CONFLICT ON CONSTRAINT user_table_username_key
		DO UPDATE
		SET full_name=EXCLUDED.full_name,
			email=EXCLUDED.email,
			institution=EXCLUDED.institution,
			country=EXCLUDED.country
		RETURNING t.id, t.username
	), ins_password AS (
		INSERT INTO private.user_password_table AS t (user_id, password_hash, is_enabled)
		SELECT insert_users.id, us->>'password_hash', true
		FROM metadata_rows s
		INNER JOIN jsonb_array_elements(NULLIF(s.users, 'null')) t(us) ON TRUE
		INNER JOIN insert_users ON insert_users.username=us->>'username'
		ON CONFLICT ON CONSTRAINT user_password_table_pkey
		DO UPDATE
		SET password_hash=EXCLUDED.password_hash,
			is_enabled=true

	), del_dac_users AS ( -- Remove users no longer in this DAC
		DELETE FROM public.dac_user_table t
		USING metadata_rows s, insert_users
		WHERE t.dac_stable_id=s.accession_id
			AND t.user_id!=insert_users.id
	), upsert AS (
		-- Insert or update users in this DAC
		INSERT INTO public.dac_user_table AS t (dac_stable_id, user_id, is_main, member_type)
		SELECT s.accession_id, insert_users.id, (us->>'is_main')::bool, (us->>'member_type')::public.member_type
		FROM metadata_rows s
		INNER JOIN jsonb_array_elements(NULLIF(s.users, 'null')) t(us) ON TRUE
		INNER JOIN insert_users ON insert_users.username=us->>'username'
		ON CONFLICT ON CONSTRAINT dac_user_table_pkey
		DO UPDATE
		SET is_main=EXCLUDED.is_main,
			member_type=EXCLUDED.member_type
		RETURNING t.user_id
	)
	SELECT COUNT(*) INTO _rows
	FROM upsert
	;

	---------------------
	-- CLEANUP orphans --
	---------------------

	-- Delete orphan dac-users
	WITH del_dac AS (
			SELECT dac.stable_id
			FROM public.dac_table dac
			LEFT JOIN public.dac_dataset_table dac_dat ON dac_dat.dac_stable_id=dac.stable_id
			WHERE dac_dat.dataset_stable_id IS NULL -- Find DACs not linked to any dataset
	)
	DELETE FROM public.dac_user_table t
	USING del_dac
	WHERE t.dac_stable_id=del_dac.stable_id
	;

	-- Delete orphan user data (oprhan means that they have no permissions and they are not members of any DAC)
	WITH no_perm_no_dac AS (
		SELECT us.id AS user_id
		FROM public.user_table us
		LEFT JOIN private.dataset_permission_table dpt ON dpt.user_id=us.id
		LEFT JOIN public.dac_user_table dac_us ON dac_us.user_id=us.id
		WHERE dpt.dataset_stable_id IS NULL -- user w/o permissions
			AND dac_us.dac_stable_id IS NULL -- user not a member of any DAC
	), del_passwords AS (
		DELETE FROM private.user_password_table t
		USING no_perm_no_dac p
		WHERE t.user_id=p.user_id

	)
	DELETE FROM public.user_key_table t
	USING no_perm_no_dac p
	WHERE t.user_id=p.user_id
	;

	-- Delete orphan users
        WITH no_perm_no_dac AS (
		SELECT us.id AS user_id
		FROM public.user_table us
		LEFT JOIN private.dataset_permission_table dpt ON dpt.user_id=us.id
		LEFT JOIN public.dac_user_table dac_us ON dac_us.user_id=us.id
		WHERE dpt.dataset_stable_id IS NULL -- user w/o permissions
			AND dac_us.dac_stable_id IS NULL -- user not a member of any DAC
	)
	DELETE FROM public.user_table t
	USING no_perm_no_dac p
	WHERE t.id=p.user_id
	;

    RETURN _rows;
END
$BODY$;

CREATE OR REPLACE FUNCTION public.process_dac_message(_json_message jsonb)
RETURNS bigint
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
        _rows bigint;
BEGIN
		-- Dacs & datasets
        WITH metadata_data(metadata_json) AS (
                SELECT (_json_message)

        ), metadata_rows AS (
                SELECT --metadata_json->>'type' AS type,
                        metadata_json->>'accession_id' AS accession_id,
                        metadata_json->>'title' AS title,
			metadata_json->>'description' AS description
                FROM metadata_data s

        ), update_dac AS (
                UPDATE public.dac_table t
                SET title=s.title,
                	description=s.description
                FROM metadata_rows s
                RETURNING t.stable_id

        )
        SELECT count(*) INTO _rows
        FROM update_dac
        ;

        RETURN _rows;
END
$BODY$;

