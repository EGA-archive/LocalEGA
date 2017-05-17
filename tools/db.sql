DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega;

\connect lega

SET TIME ZONE 'Europe/Stockholm';

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Archived', 'Error');
CREATE TYPE hash_algo AS ENUM ('md5', 'sha256');

CREATE TABLE submissions (
        id            INTEGER NOT NULL, PRIMARY KEY(id), UNIQUE (id),
	user_id       INTEGER NOT NULL,
	created_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	completed_at  TIMESTAMP WITH TIME ZONE,
	status        status
);

CREATE TABLE files (
        id           SERIAL, PRIMARY KEY(id), UNIQUE (id),
	submission_id INTEGER REFERENCES submissions (id) ON DELETE CASCADE,
	filename     TEXT NOT NULL,
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


-- Updating the timestamp when the status is modified
-- Moreover, when the status is Archived, check if we should update the associated submission completed_at
CREATE FUNCTION file_status_updated() RETURNS TRIGGER AS $update_trigger$
    DECLARE
         c INTEGER;
    BEGIN
       IF (OLD.status IS DISTINCT FROM NEW.status) THEN
          NEW.last_modified := current_timestamp;
          -- NEW.last_user := current_user;

          IF NEW.status = 'Archived' THEN
              SELECT COUNT(id) INTO c FROM files WHERE submission_id = NEW.submission_id and status != 'Archived';
              IF c = 0 THEN -- they are all archived
                 UPDATE submissions SET completed_at = current_timestamp, status = 'Archived' WHERE id = NEW.submission_id;
              END IF;
          END IF;
       END IF;
       RETURN NEW;
    END;
$update_trigger$ LANGUAGE plpgsql;

-- "Zee" Trigger... bada boom!
CREATE TRIGGER trigger_status_updated
  AFTER UPDATE ON files
  FOR EACH ROW EXECUTE PROCEDURE file_status_updated();
    
-- For an error
CREATE FUNCTION insert_error(file_id    errors.file_id%TYPE,
                             msg        errors.msg%TYPE,
                             from_user  errors.from_user%TYPE)
    RETURNS void AS $set_error$
    DECLARE 
        submission_id submissions.id%TYPE;
    BEGIN
       INSERT INTO errors (file_id,msg,from_user) VALUES(file_id,msg,from_user);
       WITH submission_id AS (
            UPDATE files SET status = 'Error' WHERE id = file_id RETURNING files.submission_id
       )
       UPDATE submissions SET status = 'Error' WHERE id = submission_id;
    END;
$set_error$ LANGUAGE plpgsql;

-- For a submission
CREATE FUNCTION insert_submission(sid submissions.id%TYPE,
                                  uid submissions.user_id%TYPE)
    RETURNS void AS $insert_submission$
    BEGIN
	INSERT INTO submissions (id, user_id) VALUES(sid, uid) ON CONFLICT (id) DO UPDATE SET created_at = DEFAULT;
    END;
$insert_submission$ LANGUAGE plpgsql;

-- For a file
CREATE FUNCTION insert_file(submission_id     files.submission_id%TYPE,
                            filename          files.filename%TYPE,
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
	INSERT INTO files (submission_id,filename,enc_checksum,enc_checksum_algo,org_checksum,org_checksum_algo,status)
	VALUES(submission_id,filename,enc_checksum,enc_checksum_algo,org_checksum,org_checksum_algo,status) RETURNING files.id
	INTO file_id;
	RETURN file_id;
    END;
$insert_file$ LANGUAGE plpgsql;

-- CREATE FUNCTION insert_filesize(file_id   files.id%TYPE,
--        			        fsize     files.filesize%TYPE)
--     RETURNS void AS $insert_filesize$
--     #variable_conflict use_column
--     BEGIN
-- 	UPDATE files SET filesize = fsize WHERE id = file_id;
--     END;
-- $insert_filesize$ LANGUAGE plpgsql;
