\connect lega

SET TIME ZONE 'Europe/Stockholm';

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Completed', 'Archived', 'Error');
-- CREATE TYPE hash_algo AS ENUM ('md5', 'sha256');

-- ##################################################
--                        FILES
-- ##################################################
CREATE TABLE IF NOT EXISTS files (
        id             SERIAL, PRIMARY KEY(id), UNIQUE (id),
	elixir_id      TEXT NOT NULL,
	inbox_path     TEXT NOT NULL,
	status         status,
	vault_path     TEXT,
	vault_filesize INTEGER,
	stable_id      TEXT,
	header         TEXT, -- crypt4gh
	created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE FUNCTION insert_file(inpath files.inbox_path%TYPE,
			    eid    files.elixir_id%TYPE,
			    sid    files.stable_id%TYPE,
			    status files.status%TYPE)
    RETURNS files.id%TYPE AS $insert_file$
    #variable_conflict use_column
    DECLARE
        file_id files.id%TYPE;
    BEGIN
	INSERT INTO files (inbox_path,elixir_id,stable_id,status)
	VALUES(inpath,eid,sid,status) RETURNING files.id
	INTO file_id;
	RETURN file_id;
    END;
$insert_file$ LANGUAGE plpgsql;

-- ##################################################
--                      ERRORS
-- ##################################################
CREATE TABLE IF NOT EXISTS errors (
        id            SERIAL, PRIMARY KEY(id), UNIQUE (id),
	file_id       INTEGER REFERENCES files (id) ON DELETE CASCADE,
	hostname      TEXT,
	error_type    TEXT NOT NULL,
	msg           TEXT NOT NULL,
	from_user     BOOLEAN DEFAULT FALSE,
	occured_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE FUNCTION insert_error(fid   errors.file_id%TYPE,
                             h     errors.hostname%TYPE,
                             etype errors.error_type%TYPE,
                             msg   errors.msg%TYPE,
                             from_user  errors.from_user%TYPE)
    RETURNS void AS $set_error$
    BEGIN
       INSERT INTO errors (file_id,hostname,error_type,msg,from_user) VALUES(fid,h,etype,msg,from_user);
       UPDATE files SET status = 'Error' WHERE id = fid;
    END;
$set_error$ LANGUAGE plpgsql;
