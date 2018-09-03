\connect lega

SET TIME ZONE 'Europe/Stockholm';

-- These are ingestion status. Add the data-out status if necessary
CREATE TYPE status AS ENUM ('Received', 'In progress', 'Completed', 'Archived', 'Ready', 'Error');
CREATE TYPE checksum_algorithm AS ENUM ('md5', 'sha256');

-- CREATE EXTENSION pgcrypto;

-- ##################################################
--                        FILES
-- ##################################################
CREATE TABLE files (
       -- Using a string and having it indexed OR using an id ? --> Much better with IDs of course
       id                   SERIAL, PRIMARY KEY(id), UNIQUE (id),
       -- file_id              VARCHAR(128) NOT NULL, PRIMARY KEY(file_id), UNIQUE (file_id),
       -- file names, paths, size, etc...
       file_name            TEXT,    -- using it as Stable ID
       file_path            TEXT,
       display_file_name    TEXT,    -- no idea what that is
       file_size            INTEGER,
       -- vault_filesize INTEGER,
       -- Crypt4GH header
       header               TEXT,
       -- Useless checksums when using Crypt4GH
       checksum                  VARCHAR(32),
       checksum_type             checksum_algorithm,
       unencrypted_checksum      VARCHAR(32),
       unencrypted_checksum_type checksum_algorithm,
       -- Status
       status               status NOT NULL,
       -- Big brother: Who and When
       created_by        TEXT,
       last_modified_by  TEXT,
       created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
       last_modified     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
)
WITH (
	OIDS=FALSE
);
-- CREATE UNIQUE INDEX file_id_idx ON files (file_id);


CREATE FUNCTION insert_file(inpath TEXT, eid TEXT)
    RETURNS files.id%TYPE AS $insert_file$
    #variable_conflict use_column
    DECLARE
        file_id files.id%TYPE;
    BEGIN
	INSERT INTO files (status) VALUES('Received') RETURNING files.id INTO file_id;
	RETURN file_id;
    END;
$insert_file$ LANGUAGE plpgsql;


-- ##################################################
--                      ERRORS
-- ##################################################
CREATE TABLE errors (
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
