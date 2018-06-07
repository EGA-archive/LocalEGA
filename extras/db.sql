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
	inbox_path     TEXT NOT NULL,
	status         status,
	vault_path     TEXT,
	vault_filesize Integer,
	stable_id      TEXT,
	header         TEXT, -- crypt4gh
	created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE FUNCTION insert_file(filename    files.filename%TYPE,
			    eid         files.elixir_id%TYPE,
			    stable_id   files.stable_id%TYPE,
			    status      files.status%TYPE)
    RETURNS files.id%TYPE AS $insert_file$
    #variable_conflict use_column
    DECLARE
        file_id files.id%TYPE;
    BEGIN
	INSERT INTO files (inbox_path,elixir_id,stable_id,status)
	VALUES(filename,eid,stable_id,status) RETURNING files.id
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

CREATE FUNCTION insert_error(file_id    errors.file_id%TYPE,
                             msg        errors.msg%TYPE,
                             from_user  errors.from_user%TYPE)
    RETURNS void AS $set_error$
    BEGIN
       INSERT INTO errors (file_id,msg,from_user) VALUES(file_id,msg,from_user);
       UPDATE files SET status = 'Error' WHERE id = file_id;
    END;
$set_error$ LANGUAGE plpgsql;
