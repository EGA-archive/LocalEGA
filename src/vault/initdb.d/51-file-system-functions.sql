-- ############################
-- Functions
-- ############################
CREATE SCHEMA IF NOT EXISTS fs; -- file system

--
-- Instead of using the postgres extension (not loaded here).
-- We hard-code the same functionality in SQL.
-- Note that this is an over-estimation:
-- the header might be in reality smaller, in case some packets are not decryptable.
--
CREATE OR REPLACE FUNCTION fs.header_size(_hd_size integer, n integer)
RETURNS integer
LANGUAGE plpgsql IMMUTABLE
AS $_$
BEGIN
	RETURN (_hd_size - 16) * n + 16;
END; $_$;

CREATE OR REPLACE FUNCTION fs.decrypted_filesize(_payload_size bigint)
RETURNS bigint
LANGUAGE plpgsql IMMUTABLE
AS $_$
DECLARE
	_nsegments  bigint;
BEGIN
	_nsegments := (_payload_size / 65564); -- truncates towards 0
	IF _payload_size % 65564 != 0 THEN
	   _nsegments := _nsegments + 1;
	END IF;
	RETURN _payload_size - (_nsegments * 28);
END; $_$;



/*
 * EGA Dist Fuse Conventions: 
 * 1xx...xx <-> EGADxx...xx
 * 2xx...xx <-> EGAFxx...xx (hot)
 * 3xx...xx <-> EGAFxx...xx (cold)
 */
CREATE OR REPLACE FUNCTION fs.dataset2ino(_name text)
RETURNS bigint
LANGUAGE plpgsql
AS $_$
BEGIN
	RETURN CAST(REPLACE (_name, 'EGAD', '1') as bigint);
END; $_$;

CREATE OR REPLACE FUNCTION fs.ino2dataset_stable_id(ino bigint)
RETURNS text
LANGUAGE plpgsql
AS $_$
BEGIN
	RETURN 'EGAD' || SUBSTRING(ino::varchar, 2);
END; $_$;

CREATE OR REPLACE FUNCTION fs.file2ino(_name text, is_cold boolean)
RETURNS bigint
LANGUAGE plpgsql
AS $_$
BEGIN
	IF is_cold
	THEN
	    RETURN CAST(REPLACE (_name, 'EGAF', '3') as bigint);
	ELSE
	    RETURN CAST(REPLACE (_name, 'EGAF', '2') as bigint);
       END IF;
END; $_$;

CREATE OR REPLACE FUNCTION fs.ino2file_stable_id(ino bigint)
RETURNS text
LANGUAGE plpgsql
AS $_$
BEGIN
	RETURN 'EGAF' || SUBSTRING(ino::varchar, 2);
END; $_$;


CREATE OR REPLACE FUNCTION fs.str2ino(_name text)
RETURNS bigint
LANGUAGE plpgsql
AS $_$
BEGIN
	IF SUBSTRING(_name, 'EGAD', 1, 4) = 'EGAD' THEN
	     RETURN CAST(REPLACE (_name, 'EGAD', '1') as bigint);
	END IF;

	IF SUBSTRING(_name, 'EGAF', 1, 4) = 'EGAF' THEN
	     RETURN CAST(REPLACE (_name, 'EGAF', '2') as bigint);
	END IF;

	-- RAISE EXCEPTION 'invalid stable id %', _name;
	RETURN NULL;
END; $_$;

CREATE OR REPLACE FUNCTION fs.ino2str(ino bigint)
RETURNS text
LANGUAGE plpgsql
AS $_$
BEGIN
	IF ino > 100000000000 AND ino < 200000000000 THEN
	    RETURN 'EGAD' || SUBSTRING(ino::varchar, 2);
	END IF;
	IF ino > 200000000000 AND ino < 400000000000 THEN -- 3-400000000000 for the cold storage
	    RETURN 'EGAF' || SUBSTRING(ino::varchar, 2);
	END IF;

	-- RAISE EXCEPTION 'invalid inode %', ino;
	RETURN NULL;
END; $_$;


-- ###################################################
--          DATASETS
-- ###################################################

CREATE OR REPLACE FUNCTION fs.lookup_dataset(_userid bigint,
       			          _dataset  varchar)
RETURNS TABLE(ino bigint, stable_id text, ctime bigint, mtime bigint, num_files int4)
LANGUAGE plpgsql AS $_$
DECLARE
    rec            record;
BEGIN

    -- Fetch the records
    FOR rec IN (

    WITH controlled_datasets AS (
    	 SELECT dt.stable_id   AS ega_stable_id,
	        dt.created_at  AS ctime,
                dt.edited_at   AS mtime,
                1              AS num
             FROM private.dataset_permission_table pt
	     INNER JOIN public.dataset_table dt ON dt.stable_id = pt.dataset_stable_id
	     WHERE pt.user_id = _userid
               --AND (pt.expires_at IS NULL OR now()::date < pt.expires_at)
                   -- no expiration or expired? Let's hope the OR is a short-circuit
               AND CASE
                       WHEN pt.expires_at IS NULL THEN TRUE -- doesn't expire
                       ELSE now()::date < pt.expires_at -- just comparing the day
 		   END
               AND CASE
                       WHEN _dataset IS NOT NULL
		       THEN pt.dataset_stable_id=_dataset -- cuz we have the dataset stable id in the perm table
                       ELSE TRUE
 		   END
	       AND dt.access_type='controlled'::public.access_type
    ), non_controlled_datasets AS (
    	 SELECT dt.stable_id   AS ega_stable_id,
                dt.created_at  AS ctime,
                dt.edited_at   AS mtime,
                1              AS num
             FROM public.dataset_table dt
             WHERE dt.access_type IN ('public'::public.access_type, 'registered'::public.access_type)
               AND CASE
                       WHEN _dataset IS NOT NULL
		       THEN dt.stable_id=_dataset
                       ELSE TRUE
		   END
    )
    SELECT * FROM controlled_datasets
    UNION
    SELECT * FROM non_controlled_datasets
    )
    LOOP
        ino := fs.dataset2ino(rec.ega_stable_id);
	stable_id := rec.ega_stable_id;
        ctime := extract(epoch from rec.ctime)::bigint; -- loose precision
        mtime := extract(epoch from rec.mtime)::bigint; --
        num_files := rec.num;
        RETURN NEXT;
    END LOOP;

END; $_$;

CREATE OR REPLACE FUNCTION fs.get_datasets(_userid     bigint,
                                _offset   bigint,
				_limit    bigint)--DEFAULT 1000000)
RETURNS TABLE(ino bigint, display_name text, ctime bigint, mtime bigint, nlink int4, size bigint)
LANGUAGE plpgsql AS $_$
BEGIN

    RETURN QUERY
    SELECT q.ino       AS ino,
    	   q.stable_id AS display_name,
           q.ctime     AS ctime,
           q.mtime     AS mtime,
	   q.num_files AS nlink,
	   1::bigint     AS size
    FROM fs.lookup_dataset(_userid, NULL) q
    WHERE --q.num_files > 0 AND
          CASE
             WHEN _offset IS NOT NULL
             THEN q.ino > _offset
	     ELSE TRUE
          END
    ORDER BY q.ino --, q.name
    LIMIT _limit;
END; $_$;



-- ###################################################
--          FILES
-- ###################################################


CREATE OR REPLACE FUNCTION fs.lookup_file(_userid            bigint,
                               _dataset_stable_id varchar,
			       _filename          varchar)
RETURNS TABLE(ino bigint, stable_id text, filesize bigint, num_datasets int4, display_name text, ctime bigint, mtime bigint, decrypted_filesize text)
LANGUAGE plpgsql AS $_$
DECLARE
	number_recipient_keys int;
	--_fileid               varchar;
	_filename_tmp         varchar;
BEGIN

	-- NOTE: _userid is already the correct DB-shifted id

    IF (SUBSTRING (_dataset_stable_id, 1, 4) != 'EGAD') THEN
	RAISE EXCEPTION 'invalid dataset id';
    END IF;

    -- get number of recipients
    SELECT count(*) INTO number_recipient_keys FROM public.header_keys WHERE user_id=_userid;

    IF number_recipient_keys IS NULL OR number_recipient_keys = 0 THEN
        RAISE EXCEPTION 'user has no encryption keys';
    END IF;

    IF _filename IS NOT NULL THEN
        --_fileid:= SUBSTRING( _filename, 1, 15);

    	-- _filename := substring(_filename from '(?(?=.*\.unavailable\.c4gh$)((.*)\.unavailable\.c4gh)|((.*)\.c4gh))$');
    	-- IF _filename IS NULL THEN
	--    RAISE EXCEPTION 'invalid filename or not a C4GH file';
    	-- END IF;
	
    	_filename := substring(_filename from '(.*)\.c4gh$'); -- remove .c4gh
    	IF _filename IS NULL THEN
	   RAISE EXCEPTION 'invalid filename or not a C4GH file';
    	END IF;
	-- Check for .unavailable
    	_filename_tmp := substring(_filename from '(.*)\.unavailable$'); -- remove .unavailable
    	IF _filename_tmp IS NOT NULL THEN
    	   _filename := _filename_tmp;
	END IF;
	RAISE NOTICE 'extracted filename: %', _filename;
    END IF;
 
    -- RAISE NOTICE 'id to use: % ', _id_to_use;

    -- We do _not_ check permission on that dataset, it's been done already
    RETURN QUERY 
	SELECT --DISTINCT 
	       fs.file2ino(ft.stable_id, false)
	                     AS ino,
               ft.stable_id AS stable_id,
	       pft.payload_size::bigint + fs.header_size(octet_length(pft.header) -- 124
                                                         , number_recipient_keys)::bigint AS filesize,
	       1::int4 AS num_datasets, -- count(distinct dft.dataset_stable_id)
	       ft.display_name || '.c4gh' AS display_name,
	       extract(epoch from pft.created_at)::bigint  AS ctime,
               extract(epoch from pft.edited_at)::bigint   AS mtime,
	       fs.decrypted_filesize(pft.payload_size::bigint)::text AS decrypted_filesize
	FROM public.dataset_table dt
	INNER JOIN public.dataset_file_table dft ON dft.dataset_stable_id = dt.stable_id
	-- no join with public.dataset_table because get_datasets() already checked if released
	INNER JOIN private.file_table pft ON pft.stable_id = dft.file_stable_id
	INNER JOIN public.file_table ft ON ft.stable_id = dft.file_stable_id
	WHERE dt.stable_id = _dataset_stable_id
	      AND CASE
                       WHEN _filename IS NOT NULL
		       THEN --dft.stable_id = SUBSTRING(_filename, 1, 15)
		            ft.display_name = _filename
                       ELSE TRUE
		  END
	;
END;
$_$;




CREATE OR REPLACE FUNCTION fs.get_files(_userid            bigint,
                             _dataset_stable_id varchar,
                             _offset            bigint,
                             _limit             bigint)
RETURNS TABLE(ino bigint, display_name text, ctime bigint, mtime bigint, nlink int4, filesize bigint, decrypted_filesize text)
LANGUAGE plpgsql AS $_$
BEGIN
    
    RETURN QUERY
    SELECT q.ino             AS ino,
           q.display_name    AS display_name,
	   q.ctime           AS ctime,
	   q.mtime           AS mtime,
	   q.num_datasets    AS nlink,
	   q.filesize        AS size,
	   q.decrypted_filesize  AS decrypted_filesize
    FROM fs.lookup_file(_userid, _dataset_stable_id, NULL) q
    WHERE --q.num_files > 0 AND
          CASE
             WHEN _offset IS NOT NULL
             THEN q.ino > _offset
	     ELSE TRUE
          END
    ORDER BY q.ino
    LIMIT _limit;
END; $_$;


--
-- The headers are re-encrypted:
-- * from the master key
-- * to the user public key
-- 

CREATE OR REPLACE FUNCTION fs.get_file_info(_username varchar,
                                 _file_ino bigint)
RETURNS TABLE(filepath text, header bytea)
LANGUAGE plpgsql AS $_$
DECLARE
	user_number_id bigint;
	_file_stable_id varchar;
BEGIN

    IF _file_ino > 300000000000 AND _file_ino < 400000000000
    THEN
       RAISE EXCEPTION 'Not available';
       -- RETURN QUERY SELECT NULL AS filepath, NULL AS header;
    END IF;

    -- Get the user_id from the name
    SELECT id INTO user_number_id
    FROM public.user_table ut
    WHERE ut.username = lower(_username);

    IF user_number_id IS NULL THEN
        RAISE EXCEPTION 'user % not found', _username;
    END IF;

    -- RAISE NOTICE 'user_number_id value is % ', user_number_id;

    _file_stable_id := fs.ino2file_stable_id(_file_ino);
    IF _file_stable_id IS NULL THEN
        RAISE EXCEPTION 'Invalid stable id for %', _file_ino;
    END IF;

    -- RAISE NOTICE 'file stable id: % ', _file_stable_id;

    -- no need to check the permissions: fuse already did that with the previous queries
    RETURN QUERY
    SELECT (pft.mount_point || '/' || pft.relative_path) AS filepath,
	   crypt4gh.header_reencrypt(pft.header,
	                             (SELECT array_agg(ukt.pubkey) FROM public.user_key_table ukt
				      WHERE ukt.type IN ('c4gh-v1'::public.key_type,'ssh-ed25519'::public.key_type)
	  			        AND ukt.pubkey IS NOT NULL
					AND ukt.user_id = user_number_id)) AS reencrypted_header
           -- we can return the payload size and real filesize too
	   -- but fuse will open the file and use lseek to the end
    FROM private.file_table pft
    WHERE pft.stable_id = _file_stable_id
    LIMIT 1; -- don't repeat file stable_id if they belong to several datasets.

END; $_$;



-- ###################################################
--          FUSE FUNCTIONS
-- ###################################################

CREATE OR REPLACE FUNCTION fs.readdir(_username  varchar,
       			   parent_ino bigint,
                           _offset    bigint,
			   _limit     bigint)--DEFAULT 1000000)
RETURNS TABLE(ino bigint, display_name text, ctime bigint, mtime bigint, nlink int4, size bigint, decrypted_filesize text, is_dir boolean)
LANGUAGE plpgsql AS $_$
DECLARE
	user_number_id        bigint;
	dataset           varchar;
BEGIN

    -- Get the user_id from the name
    SELECT id INTO user_number_id
    FROM public.user_table ut
    WHERE ut.username = lower(_username);

    IF user_number_id IS NULL THEN
        RAISE EXCEPTION 'user % not found', _username;
    END IF;
    -- RAISE NOTICE 'user_number_id value is % ', user_number_id;

    IF parent_ino = 1 THEN
        -- list datasets
	RETURN QUERY
	SELECT q.*, '1' AS decrypted_filesize, TRUE AS is_dir
        FROM fs.get_datasets(user_number_id, _offset, _limit) q;
    ELSE
	-- list files
	RETURN QUERY
	SELECT q.*, FALSE AS is_dir
        FROM fs.get_files(user_number_id, fs.ino2dataset_stable_id(parent_ino), _offset, _limit) q;
    END IF;

END;
$_$;



CREATE OR REPLACE FUNCTION fs.lookup(_username varchar,
       			  _parent_ino bigint,
			  _name varchar)
RETURNS TABLE(ino bigint, ctime bigint, mtime bigint, nlink int4, size bigint, decrypted_filesize text, is_dir boolean)
LANGUAGE plpgsql AS $_$
DECLARE
	user_number_id        bigint;
BEGIN

    -- Get the user_id from the name
    SELECT id INTO user_number_id
    FROM public.user_table ut
    WHERE ut.username = lower(_username);

    IF user_number_id IS NULL THEN
        RAISE EXCEPTION 'user % not found', _username;
    END IF;
    -- RAISE NOTICE 'user_number_id value is % ', user_number_id;

    IF _parent_ino = 1 THEN
        -- dataset lookup
	RETURN QUERY
	SELECT q.ino            AS ino,
	       q.ctime          AS ctime,
	       q.mtime          AS mtime,
	       q.num_files      AS nlink,
	       1::bigint          AS size,
	       '1'              AS decrypted_size,
	       TRUE::boolean    AS is_dir
 	FROM fs.lookup_dataset(user_number_id, _name) q
	LIMIT 1;
    ELSE
        -- file lookup
	RETURN QUERY
	SELECT q.ino            AS ino,
	       q.ctime          AS ctime,
	       q.mtime          AS mtime,
	       q.num_datasets   AS nlink,
	       q.filesize       AS size,
	       q.decrypted_filesize AS decrypted_size,
	       FALSE::boolean   AS is_dir
	FROM fs.lookup_file(user_number_id, fs.ino2dataset_stable_id(_parent_ino), _name) q
	LIMIT 1;
    END IF;

END;
$_$;



CREATE OR REPLACE FUNCTION fs.getattr(_username varchar,
       			   _ino bigint)
RETURNS TABLE(ctime bigint, mtime bigint, nlink int4, size bigint, decrypted_filesize text, is_dir boolean)
LANGUAGE plpgsql AS $_$
DECLARE
	user_number_id        bigint;
	number_recipient_keys int;
	_stable_id            varchar;
BEGIN

    -- Get the user_id from the name
    SELECT id INTO user_number_id
    FROM public.user_table ut
    WHERE ut.username = lower(_username);

    IF user_number_id IS NULL THEN
        RAISE EXCEPTION 'user % not found', _username;
    END IF;
    -- RAISE NOTICE 'user_number_id value is % ', user_number_id;

    IF _ino >= 100000000000 AND _ino < 200000000000 THEN
        -- a dataset
    	_stable_id := fs.ino2dataset_stable_id(_ino);
    	RAISE NOTICE 'looking up dataset % ', _stable_id;
	RETURN QUERY
	SELECT q.ctime          AS ctime,
	       q.mtime          AS mtime,
	       q.num_files      AS nlink,
	       1::bigint          AS size,
	       '1'              AS decrypted_size,
	       FALSE::boolean   AS is_dir
 	FROM fs.lookup_dataset(user_number_id, _stable_id) q;
	RETURN;
    END IF;

    IF _ino >= 200000000000 AND _ino < 400000000000 THEN -- _ino < 300000000000
        -- a file
	-- get number of recipients
	SELECT count(*) INTO number_recipient_keys FROM public.header_keys WHERE user_id=user_number_id;
	IF number_recipient_keys IS NULL OR number_recipient_keys = 0 THEN
            RAISE EXCEPTION 'user has no encryption keys';
        END IF;

        _stable_id := fs.ino2file_stable_id(_ino);
    	RAISE NOTICE 'looking up file %', _stable_id;

	RETURN QUERY
	SELECT extract(epoch from pft.created_at)::bigint  AS ctime,
               extract(epoch from pft.edited_at)::bigint   AS mtime,
	       1::int4 AS nlink, -- count(distinct dft.dataset_stable_id)
	       --ft.filesize::bigint - octet_length(pft.header) 
	       pft.payload_size + fs.header_size(octet_length(pft.header),
                                                    number_recipient_keys)::bigint
						           AS size,
	       fs.decrypted_filesize(pft.payload_size)::text AS decrypted_size,
	       FALSE::boolean                      AS is_dir
	FROM public.file_table ft
	INNER JOIN private.file_table pft ON pft.stable_id = ft.stable_id
	-- no join with public.dataset_table because get_datasets() already checked if released
	-- INNER JOIN private.dataset_file_table pdft ON pdft.id = dft.id
	WHERE ft.stable_id = _stable_id
	 -- AND dft.dataset_stable_id = _dataset_stable_id
	LIMIT 1;
	RETURN;
    END IF;

    --RAISE NOTICE 'invalid inode %', _ino;
    RAISE EXCEPTION 'invalid inode %', _ino;
END; $_$;




-- ###################################################
--          Stats
-- ###################################################

CREATE OR REPLACE FUNCTION fs.stats(_username varchar, _ino bigint)
RETURNS TABLE(files bigint, size bigint)
LANGUAGE plpgsql
AS $_$
BEGIN

    SELECT (count(DISTINCT dft.dataset_stable_id) + count(DISTINCT dft.stable_id))::bigint AS files,
	    sum(dft.filesize)::bigint AS size
    FROM fs.readdir(_username, 1, NULL, NULL) d
    INNER JOIN public.dataset_file_table dft ON d.display_name = dft.dataset_stable_id -- display_name is the dataset stable_id
    ;
END; $_$;




CREATE OR REPLACE FUNCTION fs.getxattr(_username varchar, _ino bigint, _name varchar)
RETURNS text
LANGUAGE plpgsql AS $_$
DECLARE
	user_number_id        bigint;
	_stable_id            varchar;
	_res                  varchar;
BEGIN

    -- Get the user_id from the name
    SELECT id INTO user_number_id
    FROM public.user_table ut
    WHERE ut.username = lower(_username);

    IF user_number_id IS NULL THEN
        RAISE EXCEPTION 'user % not found', _username;
    END IF;
    -- RAISE NOTICE 'user_number_id value is % ', user_number_id;

    IF _ino < 200000000000 OR _ino > 400000000000 THEN
        RAISE EXCEPTION 'Not a file: %', _ino;
    END IF;

    _res := '';
    IF _name = 'user.decrypted_filesize' THEN

        _stable_id := fs.ino2file_stable_id(_ino);
        -- RAISE NOTICE 'looking up file %', _stable_id;

        SELECT (fs.decrypted_filesize(pft.payload_size))::text INTO _res
	FROM public.file_table ft
	JOIN private.file_table pft ON pft.stable_id = ft.stable_id
	WHERE ft.stable_id = _stable_id
	LIMIT 1;
    END IF;


    RETURN _res;

END; $_$;
