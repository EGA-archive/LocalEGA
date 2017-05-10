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
	completed_at  TIMESTAMP WITH TIME ZONE
);

CREATE TABLE files (
        id           SERIAL, PRIMARY KEY(id), UNIQUE (id),
	submission_id INTEGER REFERENCES submissions (id) ON DELETE CASCADE,
	filename     TEXT NOT NULL,
	filehash     TEXT NOT NULL,
	hash_algo    hash_algo,
	status       status,
	error        TEXT,
	stable_id    TEXT,
	reenc_key    TEXT,
	reenc_info   TEXT,
	created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

-- The filehash is the checksum value of the original unencrypted file.
-- We do not store the checksum of the encrypted file from the inbox, as it is 
-- only interesting to check if we really received the whole file.
-- We already have that test in place, so when the latter test passes,
-- we are not any longer interested in the checksum of the encrypted file.

-- The reencryption field is used to store how the original unencrypted file was re-encrypted.
-- We gpg-decrypt the encrypted file and send the output, by blocks, to the re-encryptor.
-- The key size, the algorithm and the chunk size is recorded in the re-encrypted file (first line)
-- and in the database.


-- Updating the timestamp when the status is modified
-- Moreover, when the status is Archived, check if we should update the associated submission completed_at
CREATE FUNCTION update_last_modified() RETURNS TRIGGER AS $update_trigger$
    DECLARE
         c INTEGER;
    BEGIN
       IF (OLD.status IS DISTINCT FROM NEW.status) THEN
          NEW.last_modified := current_timestamp;
          -- NEW.last_user := current_user;

          IF NEW.status = 'Archived' THEN
              SELECT COUNT(id) INTO c FROM files WHERE submission_id = NEW.submission_id and status != 'Archived';
              IF c = 0 THEN -- they are all archived
                 UPDATE submissions SET completed_at = current_timestamp WHERE id = NEW.submission_id;
              END IF;
          END IF;
       END IF;
       RETURN NEW;
    END;
$update_trigger$ LANGUAGE plpgsql;

-- "Zee" Trigger... bada boom!
CREATE TRIGGER trigger_status_updated
  AFTER UPDATE ON files
  FOR EACH ROW EXECUTE PROCEDURE update_last_modified();
    
