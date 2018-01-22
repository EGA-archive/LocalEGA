\connect lega

SET TIME ZONE 'Europe/Stockholm';

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Completed', 'Archived', 'Error');
CREATE TYPE hash_algo AS ENUM ('md5', 'sha256');

CREATE EXTENSION pgcrypto;


-- ##################################################
--                        FILES
-- ##################################################
CREATE TABLE files (
        id             SERIAL, PRIMARY KEY(id), UNIQUE (id),
	elixir_id      TEXT NOT NULL,
	filename       TEXT NOT NULL,
	enc_checksum   TEXT,
	enc_checksum_algo hash_algo,
	org_checksum   TEXT,
	org_checksum_algo hash_algo,
	status         status,
	staging_name   TEXT,
	stable_id      TEXT,
	reenc_info     TEXT,
	reenc_size     INTEGER,
	reenc_checksum TEXT, -- sha256
	created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE FUNCTION insert_file(filename    files.filename%TYPE,
			    eid         files.elixir_id%TYPE,
			    status      files.status%TYPE)
    RETURNS files.id%TYPE AS $insert_file$
    #variable_conflict use_column
    DECLARE
        file_id files.id%TYPE;
    BEGIN
	INSERT INTO files (filename,elixir_id,status)
	VALUES(filename,eid,status) RETURNING files.id
	INTO file_id;
	RETURN file_id;
    END;
$insert_file$ LANGUAGE plpgsql;

-- ##################################################
--                      ERRORS
-- ##################################################
CREATE TABLE errors (
        id            SERIAL, PRIMARY KEY(id), UNIQUE (id),
	file_id       INTEGER REFERENCES files (id) ON DELETE CASCADE,
	msg           TEXT NOT NULL,
	from_user     BOOLEAN DEFAULT FALSE,
	occured_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

-- The reencryption field is used to store how the original unencrypted file was re-encrypted.
-- We gpg-decrypt the encrypted file and pipe the output to the re-encryptor.
-- The key size, the algorithm and the selected master key is recorded in the re-encrypted file (first line)
-- and in the database.

CREATE FUNCTION insert_error(file_id    errors.file_id%TYPE,
                             msg        errors.msg%TYPE,
                             from_user  errors.from_user%TYPE)
    RETURNS void AS $set_error$
    BEGIN
       INSERT INTO errors (file_id,msg,from_user) VALUES(file_id,msg,from_user);
       UPDATE files SET status = 'Error' WHERE id = file_id;
    END;
$set_error$ LANGUAGE plpgsql;


-- ##################################################
--        Extra Functionality
-- ##################################################

CREATE FUNCTION file_info(fname TEXT, eid TEXT)
    RETURNS JSON AS $file_info$
    #variable_conflict use_column
    DECLARE
        r RECORD;
    BEGIN
	SELECT filename, elixir_id, created_at,
	       enc_checksum, enc_checksum_algo,
	       org_checksum, org_checksum_algo,
	       status, (CASE status
	       	       	     WHEN 'Error'::status THEN
			       	          (SELECT msg FROM errors e WHERE e.file_id = f.id)  
       	       	             WHEN 'Archived'::status THEN f.stable_id
 			     ELSE status::text
	               END) AS status_message
        FROM files f WHERE f.filename = fname AND f.elixir_id = eid
	INTO STRICT r;
	RETURN row_to_json(r);
	EXCEPTION WHEN NO_DATA_FOUND THEN RAISE EXCEPTION 'File % or User % not found', fname, eid;
                  WHEN TOO_MANY_ROWS THEN RAISE EXCEPTION 'Not unique';
    END;
$file_info$ LANGUAGE plpgsql;

CREATE FUNCTION userfiles_info(eid TEXT)
    RETURNS JSON AS $file_info$
    #variable_conflict use_column
    BEGIN
    	RETURN (SELECT json_agg(t)
	        FROM (SELECT filename, elixir_id, created_at,
	                     enc_checksum, enc_checksum_algo,
	                     org_checksum, org_checksum_algo,
	                     status, (CASE status WHEN 'Error'::status THEN
			       	                       (SELECT msg FROM errors e WHERE e.file_id = f.id)  
       	       	                                  WHEN 'Archived'::status THEN f.stable_id
 			                          ELSE status::text
    		                      END) AS status_message
                      FROM files f WHERE f.elixir_id = eid) AS t);
    END;
$file_info$ LANGUAGE plpgsql;
