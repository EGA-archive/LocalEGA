DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega;

\connect lega

-- DROP TABLE IF EXISTS files;
-- DROP TABLE IF EXISTS submissions;

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
	stable_id    INTEGER,
	reencryption TEXT,
	created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

-- Updating the timestamp when the status is modified
CREATE FUNCTION update_date_modified() RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.last_modified := current_date;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trigger_status_updated
  BEFORE UPDATE ON files
  FOR EACH ROW
  WHEN (OLD.status IS DISTINCT FROM NEW.status)
  EXECUTE PROCEDURE update_date_modified();

-- Prepared Statements
PREPARE insert_submission (int, int) AS
   INSERT INTO submissions (id, user_id) VALUES($1,$2) ON CONFLICT (id) DO UPDATE SET created_at = DEFAULT;

PREPARE insert_file (int,text,text,hash_algo,status) AS
   INSERT INTO files (submission_id,filename,filehash,hash_algo,status) VALUES($1,$2,$3,$4,$5) 
   RETURNING files.id;

PREPARE update_status (int,status) AS
   UPDATE files SET status = $2 WHERE id = $1;

PREPARE set_error (int,status,text) AS
   UPDATE files SET status = $2, error = $3 WHERE id = $1;

