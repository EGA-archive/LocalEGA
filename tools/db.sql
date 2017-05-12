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
	created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE errors (
        id            SERIAL, PRIMARY KEY(id), UNIQUE (id),
	file_id       INTEGER REFERENCES files (id) ON DELETE CASCADE,
	msg           TEXT NOT NULL,
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
    
-- FOR THE ERRORS
CREATE FUNCTION set_error() RETURNS TRIGGER AS $error_trigger$
    BEGIN
       UPDATE files SET status = 'Error' WHERE id = NEW.file_id;
       UPDATE submissions SET status = 'Error' WHERE id = NEW.submission_id;
       RETURN NEW;
    END;
$error_trigger$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_on_error
  AFTER INSERT ON errors
  FOR EACH ROW EXECUTE PROCEDURE set_error(); 
