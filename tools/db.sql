DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega;

\connect lega

SET TIME ZONE 'Europe/Stockholm';

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Completed', 'Archived', 'Error');
CREATE TYPE hash_algo AS ENUM ('md5', 'sha256');

CREATE TABLE files (
        id           SERIAL, PRIMARY KEY(id), UNIQUE (id),
	filename     TEXT NOT NULL,
	user_id      TEXT NOT NULL,
	enc_checksum TEXT,
	enc_checksum_algo hash_algo,
	org_checksum TEXT,
	org_checksum_algo hash_algo,
	status       status,
	stable_id    TEXT,
	reenc_key    TEXT,
	reenc_info   TEXT,
	reenc_size   INTEGER,
	created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE errors (
        id            SERIAL, PRIMARY KEY(id), UNIQUE (id),
	file_id       INTEGER REFERENCES files (id) ON DELETE CASCADE,
	msg           TEXT NOT NULL,
	from_user     BOOLEAN DEFAULT FALSE,
	occured_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);


-- The reencryption field is used to store how the original unencrypted file was re-encrypted.
-- We gpg-decrypt the encrypted file and send the output, by blocks, to the re-encryptor.
-- The key size, the algorithm and the chunk size is recorded in the re-encrypted file (first line)
-- and in the database.


-- For an error
CREATE FUNCTION insert_error(file_id    errors.file_id%TYPE,
                             msg        errors.msg%TYPE,
                             from_user  errors.from_user%TYPE)
    RETURNS void AS $set_error$
    BEGIN
       INSERT INTO errors (file_id,msg,from_user) VALUES(file_id,msg,from_user);
       UPDATE files SET status = 'Error' WHERE id = file_id;
    END;
$set_error$ LANGUAGE plpgsql;

-- For a file
CREATE FUNCTION insert_file(filename          files.filename%TYPE,
			    user_id           files.user_id%TYPE,
			    enc_checksum      files.enc_checksum%TYPE,
			    enc_checksum_algo files.enc_checksum_algo%TYPE,
			    org_checksum      files.org_checksum%TYPE,
			    org_checksum_algo files.org_checksum_algo%TYPE,
			    status            files.status%TYPE)
    RETURNS files.id%TYPE AS $insert_file$
    #variable_conflict use_column
    DECLARE
        file_id files.id%TYPE;
    BEGIN
	INSERT INTO files (filename,user_id,enc_checksum,enc_checksum_algo,org_checksum,org_checksum_algo,status)
	VALUES(filename,user_id,enc_checksum,enc_checksum_algo,org_checksum,org_checksum_algo,status) RETURNING files.id
	INTO file_id;
	RETURN file_id;
    END;
$insert_file$ LANGUAGE plpgsql;
