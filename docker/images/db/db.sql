-- DROP DATABASE IF EXISTS lega;
-- CREATE DATABASE lega;

\connect lega

SET TIME ZONE 'Europe/Stockholm';

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Completed', 'Archived', 'Error');
CREATE TYPE hash_algo AS ENUM ('md5', 'sha256');

CREATE EXTENSION pgcrypto;


-- ##################################################
--                        USERS
-- ##################################################
CREATE TABLE users (
        id            SERIAL, PRIMARY KEY(id), UNIQUE(id),
        elixir_id     TEXT NOT NULL, UNIQUE(elixir_id),
	password_hash TEXT,
	pubkey        TEXT,
	created_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_accessed TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	expiration    INTERVAL NOT NULL,
	CHECK (password_hash IS NOT NULL OR pubkey IS NOT NULL)
);

CREATE FUNCTION sanitize_id(elixir_id     users.elixir_id%TYPE)
    RETURNS users.elixir_id%TYPE AS $sanitize_id$
    DECLARE
	eid     users.elixir_id%TYPE;
    BEGIN
        -- eid := trim(trailing '@elixir-europe.org' from elixir_id);
	eid := regexp_replace(elixir_id, '@.*', '');
	RETURN eid;
    END;
$sanitize_id$ LANGUAGE plpgsql;

CREATE FUNCTION insert_user(elixir_id     users.elixir_id%TYPE,
       		    	    password_hash users.password_hash%TYPE,
       		    	    public_key    users.pubkey%TYPE,
       		    	    exp_int       users.expiration%TYPE DEFAULT INTERVAL '1' MONTH)

    RETURNS users.id%TYPE AS $insert_user$
    #variable_conflict use_column
    DECLARE
        user_id users.elixir_id%TYPE;
	eid     users.elixir_id%TYPE;
    BEGIN
	eid := sanitize_id(elixir_id);
	INSERT INTO users (elixir_id,password_hash,pubkey,expiration) VALUES(eid,password_hash,public_key,exp_int)
	ON CONFLICT (elixir_id) DO UPDATE SET last_accessed = DEFAULT, expiration = exp_int
	RETURNING users.id INTO user_id;
	RETURN user_id;
    END;
$insert_user$ LANGUAGE plpgsql;

-- Delete other user entries that are too old
CREATE FUNCTION refresh_user(elixir_id users.elixir_id%TYPE)

    RETURNS void AS $refresh_user$
    #variable_conflict use_column
    DECLARE
	eid     users.elixir_id%TYPE;
    BEGIN
	eid := sanitize_id(elixir_id);
	UPDATE users SET last_accessed = DEFAULT WHERE elixir_id = eid;
	RETURN;
    END;
$refresh_user$ LANGUAGE plpgsql;

CREATE FUNCTION update_users() 
    RETURNS trigger AS $update_users$ 
    BEGIN
        DELETE FROM users WHERE last_accessed < current_timestamp - expiration;
	RETURN NEW;
    END;
$update_users$ LANGUAGE plpgsql;

CREATE TRIGGER delete_expired_users_trigger AFTER UPDATE ON users EXECUTE PROCEDURE update_users();

-- ##################################################
--                        FILES
-- ##################################################
CREATE TABLE files (
        id             SERIAL, PRIMARY KEY(id), UNIQUE (id),
	elixir_id      TEXT REFERENCES users (elixir_id) ON DELETE CASCADE,
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


