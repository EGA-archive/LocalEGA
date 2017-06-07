DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega;

\connect lega

SET TIME ZONE 'Europe/Stockholm';

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Completed', 'Archived', 'Error');
CREATE TYPE hash_algo AS ENUM ('md5', 'sha256');

CREATE EXTENSION pgcrypto;

CREATE TABLE users (
	id            TEXT NOT NULL PRIMARY KEY UNIQUE,
	password_hash TEXT,
	pubkey        TEXT,
	created_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	CHECK (password_hash IS NOT NULL OR pubkey IS NOT NULL)
);

CREATE TABLE files (
        id           SERIAL, PRIMARY KEY(id), UNIQUE (id),
	user_id      TEXT REFERENCES users (id) ON DELETE CASCADE,
	filename     TEXT NOT NULL,
	enc_checksum TEXT,
	enc_checksum_algo hash_algo,
	org_checksum TEXT,
	org_checksum_algo hash_algo,
	status       status,
	staging_name TEXT,
	stable_id    TEXT,
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

-- For users
CREATE FUNCTION insert_user(user_id    users.id%TYPE,
       		    	    password   users.password_hash%TYPE,
       		    	    public_key users.pubkey%TYPE)
    RETURNS void AS $insert_user$
    #variable_conflict use_column
    DECLARE
        salt TEXT;
        pw TEXT;
    BEGIN
    	pw := NULL;
        IF password != '' THEN
		SELECT gen_salt('bf', 8) INTO salt;
		SELECT crypt(password, salt) INTO pw;
	END IF;
	INSERT INTO users (id, password_hash, pubkey) VALUES(user_id, pw, public_key)
	ON CONFLICT (id) DO UPDATE SET password_hash = pw, pubkey = public_key, last_modified = DEFAULT;
	RETURN;
    END;
$insert_user$ LANGUAGE plpgsql;

-- CREATE FUNCTION get_user_by_password(password TEXT)
--     RETURNS users.id%TYPE AS $get_user$
--     DECLARE
--         res TABLE(users.id);
--     BEGIN
-- 	SELECT users.id INTO res FROM users WHERE password_hash = crypt(password,password_hash);
-- 	RETURN res;
--     END;
-- $get_user$ LANGUAGE plpgsql;

-- CREATE UNIQUE INDEX user_idx ON users(elixir_id);
