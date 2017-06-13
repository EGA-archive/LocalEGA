DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega;

\connect lega

SET TIME ZONE 'Europe/Stockholm';

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Completed', 'Archived', 'Error');
CREATE TYPE hash_algo AS ENUM ('md5', 'sha256');

CREATE EXTENSION pgcrypto;


-- ##################################################
--                        USERS
-- ##################################################
CREATE SEQUENCE IF NOT EXISTS users_id_seq INCREMENT 1 MINVALUE 1000 NO MAXVALUE START 1000 NO CYCLE;

CREATE TABLE users (
        id            INTEGER NOT NULL DEFAULT nextval('users_id_seq'::regclass), PRIMARY KEY(id), UNIQUE (id),
	elixir_id     TEXT NOT NULL UNIQUE,
	password_hash TEXT,
	pubkey        TEXT,
	seckey        TEXT,
	created_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE user_errors (
        id            SERIAL, PRIMARY KEY(id), UNIQUE (id),
	user_id       INTEGER REFERENCES users (id) ON DELETE CASCADE,
	msg           TEXT NOT NULL,
	occured_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE FUNCTION insert_user(elixir_id  users.elixir_id%TYPE)
    RETURNS users.id%TYPE AS $insert_user$
    #variable_conflict use_column
    DECLARE
        user_id users.id%TYPE;
    BEGIN
	INSERT INTO users (elixir_id) VALUES(elixir_id)
	ON CONFLICT (elixir_id) DO UPDATE SET last_modified = DEFAULT
	RETURNING users.id INTO user_id;
	RETURN user_id;
    END;
$insert_user$ LANGUAGE plpgsql;

CREATE FUNCTION update_user(user_id     users.id%TYPE,
       		    	    password    users.password_hash%TYPE,
       		    	    public_key  users.pubkey%TYPE,
       		    	    private_key users.seckey%TYPE)
    RETURNS void AS $update_user$
    #variable_conflict use_column
    DECLARE
        salt TEXT;
        pw TEXT;
    BEGIN
	SELECT gen_salt('bf', 8) INTO salt;
	SELECT crypt(password, salt) INTO pw;
	UPDATE users SET password_hash = pw, pubkey = public_key, seckey = private_key, last_modified = DEFAULT
	WHERE id = user_id;
    END;
$update_user$ LANGUAGE plpgsql;

CREATE FUNCTION insert_user_error(user_id    user_errors.user_id%TYPE,
                                  msg        user_errors.msg%TYPE)
    RETURNS void AS $set_user_error$
    BEGIN
       INSERT INTO user_errors (user_id,msg) VALUES(user_id,msg);
    END;
$set_user_error$ LANGUAGE plpgsql;

-- ##################################################
--                        FILES
-- ##################################################
CREATE TABLE files (
        id             SERIAL, PRIMARY KEY(id), UNIQUE (id),
	user_id        INTEGER REFERENCES users (id) ON DELETE CASCADE,
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

